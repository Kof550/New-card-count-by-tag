from aqt import mw
from aqt.qt import Qt, QAction, QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QComboBox, QLineEdit

class TagsDialog(QDialog):
    def __init__(self):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMaximizeButtonHint)
        self.setWindowTitle("Número de Cards por Tag")
        self.setMinimumSize(600, 400)

        # Layout principal
        layout = QVBoxLayout()

        # Título
        label = QLabel("Número de cartões novos, a aprender e a revisar por tag hoje:")
        layout.addWidget(label)

        # Campo de pesquisa
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Pesquisar tag...")
        self.search_box.textChanged.connect(self.update_table)
        layout.addWidget(self.search_box)

        # Combo box de ordenação
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Ordenar por Número de Cards Novos", "new_cards")
        self.sort_combo.addItem("Ordenar por Número de Cards a Aprender", "learn_cards")
        self.sort_combo.addItem("Ordenar por Número de Cards a Revisar", "review_cards")
        self.sort_combo.addItem("Ordenar por Nome da Tag", "tag_name")
        self.sort_combo.setCurrentIndex(0)
        self.sort_combo.currentIndexChanged.connect(self.update_table)
        layout.addWidget(self.sort_combo)

        # Área da tabela
        self.table_widget = QWidget()
        self.table_layout = QVBoxLayout()
        self.html_label = QLabel()
        self.html_label.setOpenExternalLinks(True)
        self.table_layout.addWidget(self.html_label)
        self.table_widget.setLayout(self.table_layout)

        # Área de rolagem
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.table_widget)
        layout.addWidget(self.scroll_area)

        # Define o layout
        self.setLayout(layout)

        # Atualiza a tabela inicial
        self.update_table()

    def update_table(self):
        search_term = self.search_box.text().lower()
        order_by = self.sort_combo.currentData()

        # Inicializa os dicionários de contagem de tags
        tag_new_cards_count = {tag: 0 for tag in mw.col.tags.all()}
        tag_learn_cards_count = {tag: 0 for tag in mw.col.tags.all()}
        tag_review_cards_count = {tag: 0 for tag in mw.col.tags.all()}

        # Inicializa dicionários de contagem individual
        individual_new_cards_count = {tag: 0 for tag in mw.col.tags.all()}
        individual_learn_cards_count = {tag: 0 for tag in mw.col.tags.all()}
        individual_review_cards_count = {tag: 0 for tag in mw.col.tags.all()}

        new_card_ids = set(mw.col.findCards("is:new"))
        learn_card_ids = set(mw.col.findCards("is:learn"))
        review_card_ids = set(mw.col.findCards("is:review prop:due=0"))

        all_card_ids = new_card_ids | learn_card_ids | review_card_ids

        for card_id in all_card_ids:
            card = mw.col.getCard(card_id)
            note = mw.col.getNote(card.nid)

            if note:
                for tag in note.tags:
                    # Atualiza a contagem individual (sem considerar a hierarquia de subtags)
                    if card_id in new_card_ids:
                        individual_new_cards_count[tag] += 1
                    if card_id in learn_card_ids:
                        individual_learn_cards_count[tag] += 1
                    if card_id in review_card_ids:
                        individual_review_cards_count[tag] += 1

                    # Atualiza a contagem absoluta (considerando a hierarquia de tags)
                    tag_parts = tag.split("::")
                    for i in range(len(tag_parts)):
                        ancestor_tag = "::".join(tag_parts[:i+1])
                        if ancestor_tag in tag_new_cards_count:
                            if card_id in new_card_ids:
                                tag_new_cards_count[ancestor_tag] += 1
                            if card_id in learn_card_ids:
                                tag_learn_cards_count[ancestor_tag] += 1
                            if card_id in review_card_ids:
                                tag_review_cards_count[ancestor_tag] += 1

        # Filtra as tags
        filtered_tags = [tag for tag in tag_new_cards_count.keys() if search_term in tag.lower()]

        # Ordenação
        if order_by == "tag_name":
            sorted_tags = sorted(filtered_tags)
        else:
            sorted_tags = sorted(
                filtered_tags,
                key=lambda tag: (
                    tag_new_cards_count[tag] if order_by == "new_cards" else
                    tag_learn_cards_count[tag] if order_by == "learn_cards" else
                    tag_review_cards_count[tag]
                ),
                reverse=True
            )

        # Totais
        total_new_cards = sum(tag_new_cards_count[tag] for tag in filtered_tags)
        total_learn_cards = sum(tag_learn_cards_count[tag] for tag in filtered_tags)
        total_review_cards = sum(tag_review_cards_count[tag] for tag in filtered_tags)

        # Geração da tabela HTML
        html = """
        <html>
        <body>
        <table border='1' style='width: 100%; border-collapse: collapse; font-size: 16px;'>
        <tr>
            <th style='width: 40%; padding: 10px;'>Tag</th>
            <th style='width: 10%; padding: 10px;'>Novos (Abs)</th>
            <th style='width: 10%; padding: 10px;'>A Aprender (Abs)</th>
            <th style='width: 10%; padding: 10px;'>Revisão (Abs)</th>
            <th style='width: 10%; padding: 10px;'>Novos (Ind)</th>
            <th style='width: 10%; padding: 10px;'>A Aprender (Ind)</th>
            <th style='width: 10%; padding: 10px;'>Revisão (Ind)</th>
        </tr>
        """

        for tag in sorted_tags:
            html += f"<tr><td style='padding: 10px;'>{tag}</td><td style='padding: 10px;'>{tag_new_cards_count[tag]}</td><td style='padding: 10px;'>{tag_learn_cards_count[tag]}</td><td style='padding: 10px;'>{tag_review_cards_count[tag]}</td><td style='padding: 10px;'>{individual_new_cards_count[tag]}</td><td style='padding: 10px;'>{individual_learn_cards_count[tag]}</td><td style='padding: 10px;'>{individual_review_cards_count[tag]}</td></tr>"
        
        html += f"""
        <tr>
            <td style='padding: 10px; font-weight: bold;'>Totais</td>
            <td style='padding: 10px; font-weight: bold;'>{total_new_cards}</td>
            <td style='padding: 10px; font-weight: bold;'>{total_learn_cards}</td>
            <td style='padding: 10px; font-weight: bold;'>{total_review_cards}</td>
            <td colspan='3'></td>
        </tr>
        </table>
        </body>
        </html>
        """

        self.html_label.setText(html)

def open_tags_dialog():
    global tags_dialog
    tags_dialog = TagsDialog()
    tags_dialog.showMaximized()

def add_tags_menu():
    action = QAction("TAG", mw)
    action.triggered.connect(open_tags_dialog)

    # Adiciona o item ao menu
    menu_bar = mw.menuBar()
    tools_menu_action = mw.form.menuTools.menuAction()
    menu_bar.insertAction(tools_menu_action, action)

add_tags_menu()
