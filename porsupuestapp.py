import flet as ft
import csv
from datetime import datetime
from weasyprint import HTML
from jinja2 import Environment, BaseLoader
import os
import json

class BillingCalculator:
    def __init__(self):
        self.trabajo_title = ""
        self.concepts = []
        self.totals = {}
        self.units = {}
        self.prices = {}
        self.subtotal = 0
        self.total = 0
        self.irpf = 0
        self.iva = 0
        self.invoice_counter_file = "invoice_counter.json"

    def calculate_subtotal(self):
        self.subtotal = round(sum(self.totals.values()),3)

    def calculate_total(self):
        iva_amount = round(self.subtotal * (self.iva / 100), 3) if self.iva else 0
        irpf_amount = round(self.subtotal * (self.irpf / 100), 3) if self.irpf else 0
        self.total = round(self.subtotal + iva_amount - irpf_amount, 3)


    def load_invoice_counter(self):
        if os.path.exists(self.invoice_counter_file):
            with open(self.invoice_counter_file, "r") as f:
                data = json.load(f)
        else:
            data = {"year": datetime.now().year, "counter": 0}
        return data

    def save_invoice_counter(self, data):
        with open(self.invoice_counter_file, "w") as f:
            json.dump(data, f)

    def generate_invoice_number(self):
        today = datetime.now()
        current_year = today.year
        data = self.load_invoice_counter()

        if data["year"] != current_year:
            data["year"] = current_year
            data["counter"] = 1
        else:
            data["counter"] += 1
        self.save_invoice_counter(data)
        return f"{current_year}-{data['counter']:03d}"

    def get_current_date(self):
        return datetime.now().strftime("%d/%m/%Y")


    def generate_invoice(self, output_folder, professional_data, client_data, include_invoice_number=True):
        self.calculate_subtotal()
        self.calculate_total()

        if include_invoice_number:
            invoice_number = self.generate_invoice_number()
        else:
            invoice_number = ""
        current_date = self.get_current_date()

        template = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <h2>{{ trabajo_title }}</h2>
            {% if invoice_number %}
                <h4>{{ invoice_number }}</h4>
            {% endif %}
            </h4>{{ current_date }}</h4>
            <title>Factura</title>
            <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 16px;
            }
            main {
                padding: 50px;
            }

            #primera {
                display: flex;
                justify-content: space-between;  
            }

            #datos_profesional {
                text-align: left;
                width: 40%;
                font-size: 20px;
            }
            #datos_cliente {
                text-align: right;
                width: 40%;
                font-size: 20px;
            }

            .nom_empresa {
                font-size: 24px;
                color: #1183b8;
                border-bottom: 2px solid #1183b8;
            }
            table{
                margin-top: 50px;
                border: 2px;
                width: 100%;
                border-collapse: collapse;
            }
            .tres_columnas {
                text-align: right;
            }

            .table_left{
                text-align: left;
            }
            .table_center{
                text-align: center;
            }
            .table_right{
                text-align: right;
            }
            td, th {
                border: 1px solid black;
                padding: 5px;
            }

            thead{
                background-color: #1183b8;
                color: white;
            }

            .total{
                font-size: 20px;
                font-weight: bold;
            }
            #pago{
                margin-top: 50px;
                margin-bottom: 50px;
            }
            #firma{
                margin-top: 50px;
                height: 200px;
            }
            h2 {
                margin-top: 20px;
                margin-bottom: 10px;
                font-size: 22px;
                color: #1183b8;
            }
            </style>
        </head>
        <body>
            <main>
            <section id="primera">
                <div id="datos_profesional">
                <p class="nom_empresa">{{ professional_data.Name }}</p>
                <p>{{ professional_data.Address }}</p>
                <p>{{ professional_data.CP }}</p>
                <p>{{ professional_data.Phone }}</p>
                <p>{{ professional_data.Email }}</p>
                <p>{{ professional_data.Portfolio }}</p>
                <p>CIF: {{ professional_data.CIF }}</p>
                </div>
                <div id="datos_cliente">
                <p class="nom_empresa">{{ client_data.Name }}</p>
                <p>{{ client_data.Address }}</p>
                <p>{{ client_data.CP }}</p>
                <p>{{ client_data.Phone }}</p>
                <p>{{ client_data.Email }}</p>
                <p>CIF: {{ client_data.CIF }}</p>
                </div>
            </section>

            <section id="segona">
                <table>
                <thead>
                    <tr>
                    <th class="table_left">Descripción</th>
                    <th class="table_center">Unidades</th>
                    <th class="table_right">Precio unitario</th>
                    <th class="table_right">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for concept in concepts %}
                    <tr>
                    <td class="table_left">{{ concept }}</td>
                    <td class="table_center">{{ units[concept] }}</td>
                    <td class="table_right">{{ prices[concept] }}€</td>
                    <td class="table_right">{{ totals[concept] | round(3) }}€</td>
                    </tr>
                    {% endfor %}
                    <tr>
                    <td class="tres_columnas" colspan="3">Subtotal</td>
                    <td class="table_right">{{ subtotal | round(3) }}€</td>
                    </tr>
                    <tr>
                    {% if iva and iva != 0 %}
                    <tr>
                        <td class="tres_columnas" colspan="3">IVA ({{ iva }}%)</td>
                        <td class="table_right">{{ subtotal * iva / 100 | round(3) }}€</td>
                    </tr>
                    {% endif %}
                    {% if irpf and irpf != 0 %}
                    <tr>
                        <td class="tres_columnas" colspan="3">IRPF (-{{ irpf }}%)</td>
                        <td class="table_right">-{{ subtotal * irpf / 100 | round(3) }}€</td>
                    </tr>
                    {% endif %}
                    </tr>
                    <tr>
                    <td class="tres_columnas total" colspan="3">Total</td>
                    <td class="table_right total">{{ total | round(3) }}€</td>
                    </tr>
                </tbody>
                </table>
            </section>
            <section id="pago">
                <p>Datos de pago:</p>
                <p>IBAN: {{ professional_data.IBAN }}</p>
                <p>SWIFT/BIC: {{ professional_data.SWIFT }}</p>
            </section>
            <section id="firma">
                <p>Firma:</p>
            </section>
            </main>
        </body>
        </html>
        """

        env = Environment(loader=BaseLoader())
        template = env.from_string(template)
        html_out = template.render(
            professional_data=professional_data,
            client_data=client_data,
            trabajo_title=self.trabajo_title,
            concepts=self.concepts,
            units=self.units,
            prices=self.prices,
            totals=self.totals,
            subtotal=self.subtotal,
            irpf=self.irpf,
            iva=self.iva,
            total=self.total,
            invoice_number=invoice_number,
            current_date=current_date
        )

        filename = f"invoice_{invoice_number if include_invoice_number else 'sin_numero'}.pdf"
        filepath = os.path.join(output_folder, filename)

        HTML(string=html_out).write_pdf(filepath)
        return filepath

class ProfessionalDataManager:
    def __init__(self):
        self.fields = ["Name", "Address", "CP", "CIF", "Phone", "Email", "Portfolio", "IBAN", "SWIFT"]
        self.data = {field: "" for field in self.fields}
        self.file_path = "professional_data.csv"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.data.update(row)

    def save_data(self):
        with open(self.file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.fields)
            writer.writeheader()
            writer.writerow(self.data)

class ClientDataManager:
    def __init__(self):
        self.fields = ["Name", "Address", "CP", "Phone", "Email", "CIF"]
        self.clients = []
        self.current_client = {}
        self.file_path = "clients_data.csv"
        self.load_clients()

    def load_clients(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, mode="r") as file:
                reader = csv.DictReader(file)
                self.clients = [row for row in reader]

    def add_client(self, client_data):
        self.clients.append(client_data)
        self.current_client = client_data
        self.save_clients()

    def save_clients(self):
        with open(self.file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(self.clients)

    def select_client(self, index):
        if 0 <= index < len(self.clients):
            self.current_client = self.clients[index]
            return self.current_client
        return None

def main(page: ft.Page):
    page.title = "Porsupuestapp"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.min_width = 750
    page.window.min_height = 700
    page.window.height = 750
    page.window.width = 700
    page.window.resizable = False,
    page.window.top = True,
    page.padding = 10
    page.scroll = False
    page.expand = True
    page.theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=ft.cupertino_colors.ACTIVE_BLUE,
    ))


    calculator = BillingCalculator()
    professional_manager = ProfessionalDataManager()
    client_manager = ClientDataManager()

    def update_totals():
        calculator.calculate_subtotal()
        calculator.calculate_total()
        subtotal_text.value = f"Subtotal: {calculator.subtotal:.2f}€"
        total_text.value = f"Total: {calculator.total:.2f}€"
        page.update()

    def add_concept_row(concept):
        def update_total(e):
            if units.value and price.value:
                calculator.units[concept] = round(float(units.value),2)
                calculator.prices[concept] = round(float(price.value),2)
                calculator.totals[concept] = round(calculator.units[concept] * calculator.prices[concept],2)
                total.value = f"{calculator.totals[concept]:.2f}€"
                update_totals()

        units = ft.TextField(label="Units", width=100, on_change=update_total, suffix_text="h")
        price = ft.TextField(label="Price", width=100, on_change=update_total, suffix_text="€")
        total = ft.Text(f"{calculator.totals.get(concept, 0):.2f}€", width=100)

        return ft.Row([
            ft.Text(concept, width=150, size=16, weight=ft.FontWeight.BOLD),
            units,
            price,
            total
        ], alignment=ft.MainAxisAlignment.CENTER)

    def add_new_concept(e):
        new_concept = new_concept_name.value
        if new_concept and new_concept not in calculator.concepts:
            calculator.concepts.append(new_concept)
            calculator.totals[new_concept] = 0
            calculator.units[new_concept] = 0
            calculator.prices[new_concept] = 0
            concept_rows.controls.append(add_concept_row(new_concept))
            new_concept_name.value = ""
            page.update()

    def select_client(e):
        if client_dropdown.value:
            selected_index = int(client_dropdown.value.split(':')[0])
            selected_client = client_manager.select_client(selected_index)
            if selected_client:
                update_client_fields(selected_client)
                page.update()

    def update_client_fields(client_data):
        for field in client_manager.fields:
            client_fields[field].value = client_data.get(field, '')
        page.update()

    def generate_invoice(include_invoice_number=True):
        output_folder = os.path.expanduser("~/Desktop")
        filepath = calculator.generate_invoice(
            output_folder,
            professional_manager.data,
            client_manager.current_client,
            include_invoice_number=include_invoice_number
        )
        page.overlay.append(ft.SnackBar(content=ft.Text(f"Invoice saved: {filepath}")))
        page.update()

    def save_professional_data():
        for field, control in zip(professional_manager.fields, professional_fields):
            professional_manager.data[field] = control.value
        professional_manager.save_data()
        page.overlay.append(ft.SnackBar(content=ft.Text("Professional data saved successfully")))
        page.update()

    def update_tax_values(e):
        try:
            calculator.irpf = float(irpf_field.value) if irpf_field.value else 0
            calculator.iva = float(iva_field.value) if iva_field.value else 0
            update_totals()
        except ValueError:
            page.overlay.append(ft.SnackBar(content=ft.Text("Please enter valid numbers for taxes")))
            page.update()

    # Billing Tab Content
    trabajo_title = ft.TextField(label="Project", value=calculator.trabajo_title, on_change=lambda e: setattr(calculator, 'trabajo_title', e.control.value))
    concept_rows = ft.Column(spacing=10)
    new_concept_name = ft.TextField(label="New Concept", expand=True)
    add_concept_button = ft.FloatingActionButton("Add Concept", on_click=add_new_concept, icon=ft.icons.ADD, bgcolor=ft.cupertino_colors.ACTIVE_BLUE, foreground_color=ft.colors.WHITE)

    concept_rows.controls.extend([
        ft.Row([new_concept_name, add_concept_button], alignment=ft.MainAxisAlignment.CENTER),
    ])

    subtotal_text = ft.Text(f"Subtotal: {calculator.subtotal:.2f}€", size=16, weight=ft.FontWeight.BOLD)
    total_text = ft.Text(f"Total: {calculator.total:.2f}€", size=24, weight=ft.FontWeight.BOLD)

    irpf_field = ft.TextField(label="IRPF (%)", value=str(calculator.irpf), width=100, on_change=update_tax_values)
    iva_field = ft.TextField(label="IVA (%)", value=str(calculator.iva), width=100, on_change=update_tax_values)

#Ordenar alfabéticamente los clientes
    sorted_clients = sorted(client_manager.clients, key=lambda client: client['Name'].lower())

    # Client Data Tab Content
    client_dropdown = ft.Dropdown(
        label="Select Client",
        options=[ft.dropdown.Option(str(i), client['Name']) for i, client in enumerate(sorted_clients)],
        #options=[ft.dropdown.Option(str(i), client['Name']) for i, client in enumerate(client_manager.clients)],
        on_change=select_client,
        border_color=ft.colors.ON_SURFACE,
        border_width=1,
        focused_border_color=ft.cupertino_colors.ACTIVE_BLUE,
        filled=True,
        bgcolor=ft.colors.SURFACE,
        focused_bgcolor=ft.colors.SURFACE,
        dense=False,
        width=300,
        
    )

    client_fields = {field: ft.TextField(label=field, value=client_manager.current_client.get(field, '') if client_manager.current_client else '') for field in client_manager.fields}

    # Professional Data Tab Content
    professional_fields = [ft.TextField(label=field, value=professional_manager.data.get(field, '')) for field in professional_manager.fields]

    # Buttons
    generate_budget_button = ft.ElevatedButton(
        "Budget", 
        on_click=lambda _: generate_invoice(include_invoice_number=False),
        style=ft.ButtonStyle(color= "white", bgcolor={"": "black"}, overlay_color=ft.cupertino_colors.ACTIVE_BLUE, side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.cupertino_colors.BLACK),ft.ControlState.HOVERED: ft.BorderSide(1, ft.cupertino_colors.ACTIVE_BLUE)})
    )
    generate_invoice_button = ft.ElevatedButton(
        " Billing ", 
        on_click=lambda _: generate_invoice(include_invoice_number=True),
        style=ft.ButtonStyle(color= "white", bgcolor={"": "black"}, overlay_color=ft.cupertino_colors.ACTIVE_BLUE, side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.cupertino_colors.BLACK),ft.ControlState.HOVERED: ft.BorderSide(1, ft.cupertino_colors.ACTIVE_BLUE)})
    )
    save_client_button = ft.ElevatedButton("Save Client", on_click=lambda _: client_manager.add_client({field: control.value for field, control in client_fields.items()}), style=ft.ButtonStyle(color= "white", bgcolor={"": "black"}, overlay_color=ft.cupertino_colors.ACTIVE_BLUE, side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.colors.BLACK),ft.ControlState.HOVERED: ft.BorderSide(1, ft.cupertino_colors.ACTIVE_BLUE)}))
    save_professional_button = ft.ElevatedButton("Save Professional Data", on_click=lambda _: save_professional_data(), style=ft.ButtonStyle(color= "white", bgcolor={"": "black"}, overlay_color=ft.cupertino_colors.ACTIVE_BLUE, side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.colors.BLACK),ft.ControlState.HOVERED: ft.BorderSide(1, ft.cupertino_colors.ACTIVE_BLUE)}))


    # Create tabs
    billing_tab = ft.Tab(
    text="Billing",
    content=ft.Container(
        padding=40,
        margin=40,
        expand=True,
        content=ft.Column([
            trabajo_title,
            concept_rows,
            ft.Row([
                subtotal_text,
            ], alignment=ft.MainAxisAlignment.START),
            ft.Row([
                irpf_field,
                iva_field,
            ], alignment=ft.MainAxisAlignment.CENTER),
            total_text,
            ft.Row([
            generate_budget_button,
            generate_invoice_button],alignment=ft.MainAxisAlignment.CENTER)
        ], scroll=ft.ScrollMode.HIDDEN)
        )
    )

    client_tab = ft.Tab(
        text="Client Data",
        content=ft.Container(
        padding=10,
        margin=10,
        content=ft.Column([
            client_dropdown,
            *client_fields.values(),
            save_client_button,
        ], alignment=ft.MainAxisAlignment.START, spacing=10)
    ))

    professional_tab = ft.Tab(
        text="Professional Data",
        content=ft.Container(
        padding=10,
        margin=10,
        content=ft.Column([
            *professional_fields,
            save_professional_button,
        ], alignment=ft.MainAxisAlignment.START, spacing=10)
    ))

    # Create tabs
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        indicator_padding=4,
        expand=2,
        scrollable=True,
        #adaptive=True,
        divider_height=0,
        label_color=ft.cupertino_colors.ACTIVE_BLUE,
        unselected_label_color="BLACK",
        indicator_color=ft.cupertino_colors.ACTIVE_BLUE,
        tabs=[billing_tab, client_tab, professional_tab],
    )
    page.add(tabs)

ft.app(target=main)