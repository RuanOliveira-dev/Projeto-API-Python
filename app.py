from flask import Flask, request, jsonify #Importação do framework Flask, função request (recebe dados da requisição)
from flask_sqlalchemy import SQLAlchemy #Importação do SQLAlchemy (ORM)
from flask_cors import CORS #importando o módulo CORS
from flask_login import UserMixin, login_user #Importando o UserMixin, login_user para a autenticação do usuário
from flask_login import LoginManager, login_required, logout_user, current_user #Importanto o LoginManager, login_required para a autenticação do usuário e o current_user que nos dá acesso ao usuário logado no momento

app = Flask(__name__) #Instância (objeto definido pela classe) do Flask
app.config["SECRET_KEY"] = "admin0011" #"Chave secreta" que o LoginManager vai utilizar para a autenticação
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db" #Configurando o caminho do banco de dados

login_manager = LoginManager() #Váriavel que vai gerenciar todos os usuários cadastrados
db = SQLAlchemy(app) #Iniciando a conexão com o banco de dados
login_manager.init_app(app) #Recebendo a aplicação como parâmetro
login_manager.login_view = "login" #Recebendo a rota de login (via)
CORS(app) #Colocando o código para executar no swagger também

#MODELAGEM DO BANCO DE DADOS

#Criando o modelo do usuário
#User (id, username, password, cart)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True) #Coluna do id
    username = db.Column(db.String(80), nullable = False, unique = True) #Coluna do nome do usuário
    password = db.Column(db.String(80), nullable = False) #Coluna da senha do usuário
    cart = db.relationship("CartItem", backref = "user", lazy = True)  #Cria uma relação entre o CartItem e o User

#Criando o modelo do produto
#Produto (id, name, price, description)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key = True) #Coluna do id (chave primária)
    name = db.Column(db.String(120), nullable = False) #Coluna do nome (Não nulo)
    price = db.Column(db.Float, nullable = False) #Coluna do preço (Não nulo)
    description = db.Column(db.Text, nullable = True) #Coluna da descrição (Opcional)

#Criando o modelo do carrinho
#Carrinho(id, user_id, product_id)
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key = True) #Coluna do id do usuário
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False) #Coluna do usuário que está acessando o carrinho (Chave estrangeira)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable = False) #Coluna do produto que será adicionado do carrinho (Chave estrangeira)

#Autenticação
#Definindo função de autenticação
@login_manager.user_loader
def load_user(user_id): #Função que recebe o id do usuário
    """Essa função existe pois toda vez que fizermos uma requisição em uma rota protegida, 
    o '@login_required' vai precisar recuperar o usuário que está acessando esta rota, e ele
    fará isso por meio desta função """
    return User.query.get(int(user_id)) #Retorna o usuário

#Definnindo rota de logout do usuário
@app.route("/logout", methods = ["POST"])
@login_required #Para acessar a rota de logout, primeiramente o usuário deve estar já logado
def logout(): #Criando função para fazer o logout
    logout_user() #Método para "desautenticar" o usuário
    return jsonify({"message" : "Logout successfully"}), 200

#Definindo a rota de login do usuário  
@app.route("/login", methods = ["POST"])
def login(): #Criando a função para fazer o login
    data = request.json #Recebe os dados da requisição
    user = User.query.filter_by(username = data.get("username")).first() #Variável que recupera o username no banco de dados
    if user and data.get("password") == user.password: #Condicional que verifica se o username e a password são iguais aos cadastrados no banco de dados
            login_user(user) #Caso todos os dados estejam corretos, autentica o usuário
            return jsonify({"message" : "Logged in successfully"}), 200 #Retorno positivo da função
    return jsonify({"message" : "Unautorized. Invalid credentials"}), 401 #Retorno caso o user digite credenciais erradas

#Definindo a rota para a adição de produtos
@app.route("/api/products/add", methods = ["POST"]) #Local da rota e o método utilizado
@login_required #Declarando a autenticação obrigatória para acessar a rota
def add_product(): #Função para adicionar produtos
    data = request.json #Recebe os dados da requisição em json
    if "name" in data and "price" in data: #Condicional que verifica se as chaves nome e preço existem
        product = Product(name = data["name"], price = data["price"], description = data.get("description", "")) #Obtendo dados do produto
        db.session.add(product) #Adicionando o produto ao banco de dados
        db.session.commit() #Efetiva as alterações feitas no banco de dados
        return jsonify({"message" : "Product added successfully!"}), 200 #Retorno do cadastro de produtos
    return jsonify({"message" : "invalid product data"}), 400 #Retorno do possível erro por faltas de dados
    
#Definindo a rota para a deleção de produtos pelo id
@app.route("/api/products/delete/<int:product_id>", methods = ["DELETE"]) #Local da rota e o método utilizado
@login_required #Declarando a autenticação obrigatória para acessar a rota
def delete_product(product_id): #Função para deletar produtos
    product = Product.query.get(product_id) #Váriavel que busca o id do produto
    if product: #Condicional para verificar se o id existe
        db.session.delete(product) #Deletando o produto
        db.session.commit() #Efetuando as alterações feitas no banco de dados
        return jsonify({"message" : "Product deleted succesfully"}), 200 #Retorno da deleção do produto
    return jsonify({"message" : "Product not found"}), 404 #Retorno do possível erro por não encontrar o id

#Definindo rota para recuperação de detalhes do produto pelo id
@app.route("/api/products/<int:product_id>", methods = ["GET"])
def get_product_details(product_id): #Função para recuperar detalhes dos produtos
    product = Product.query.get(product_id) #Variável que busca o id do produto
    if product: #Condicional que verifica se o id existe
        #Retorno da função
        return jsonify({
            "id" : product.id,
            "name" : product.name,
            "price" : product.price, 
            "description" : product.description
        }), 200
    return jsonify({"message" : "Product not found"}), 404 #Retorno da função caso não encontre o produto

#Definindo rota para atualizar informações de um produto pelo id
@app.route("/api/products/update/<int:product_id>", methods = ["PUT"])
@login_required #Declarando a autenticação obrigatória para acessar a rota
def update_product(product_id): #Função para atulizar dados do produto
    product = Product.query.get(product_id) #Váriavel que busca o id do livro
    if not product: #Condicional que verifica se o livro está sem dados
        return jsonify({"message" : "Product not found"}), 404 #Retorno da função caso não encontre o produto
    
    data = request.json #Recuperando os dados requisitados

    #Condicionais que verificam as dados e as altera os dados antigos pelos dados recebidos
    if "name" in data:
        product.name = data["name"]

    if "price" in data:
        product.price = data["price"]

    if "description" in data:
        product.description = data["description"]

    db.session.commit() #Efetuando as alterações no banco
    return jsonify({"message" : "Product updated successfully"}), 200 #Retorno de sucesso na função

#Definindo rota para a visualização de todos os produtos do banco de dados
@app.route("/api/products", methods = ["GET"])
def get_products(): #Função para recuperar todos os produtos do banco de dados
    products = Product.query.all() #Váriavel que retorna todos os produtos cadastrados
    products_list = [] #Lista onde ficará cada produto
    #Laço for para recuperar cada produto do banco de dados
    for product in products:
        product_data = {
            "id" : product.id,
            "name" : product.name,
            "price" : product.price, 
            "description" : product.description
        }
        products_list.append(product_data) #Adiciona os produtos 1 por 1 à lista
    return jsonify(products_list) #Retorno da lista de produtos


#Carrinho/Checkout
#Definindo a rota para adicionar produtos ao carrinho
@app.route("/api/cart/add/<int:product_id>", methods = ["POST"])
@login_required #Declarando a autenticação obrigatória para acessar a rota
def add_to_cart(product_id): #Função para adicionar produtos ao carrinho
    #Para adicionar algo ao carrinho, é necessário o usuário e o produto
    #User
    user = User.query.get(int(current_user.id)) #Variável que recupera o id do usuário
    #Product
    product = Product.query.get(int(product_id)) #Variável que recupera o id do produto
    
    if user and product: #Condicional que verifica se o usuário e o produto existem
        cart_item = CartItem(user_id = user.id, product_id = product.id) #Variável que obtém o id do usuário e do produto
        db.session.add(cart_item) #Adicionando o item ao carrinho
        db.session.commit() #Efetuando as alterações no banco de dados
        return jsonify({"message" : "Item added to the cart successfully"}), 200 #Retorno da função
    return jsonify({"message" : "Failed to add item to the cart"}), 400 #Retorno da função caso tenha ocorrido um erro

#Definindo a rota para deletar produtos do carrinho
@app.route("/api/cart/remove/<int:product_id>", methods = ["DELETE"])
@login_required #Declarando a autenticação obrigatória para acessar a rota
def remove_from_cart(product_id): #Função para deletar produtos do carrinho
    cart_item = CartItem.query.filter_by(user_id = current_user.id, product_id = product_id).first() #Variável que recupera o id do usuário e do produto 
    if cart_item: #Condicional que verifica se o item do carrinho existe
        db.session.delete(cart_item) #Deletando o item do carrinho
        db.session.commit() #Efetuando as alterações no banco de dados
        return jsonify({"message" : "Item removed from the cart successfully"}), 200 #Retorno da função
    return jsonify({"message" : "Failed to remove item from the cart"}), 400 #Retorno da função caso tenha ocorrido um erro

#Definindo a rota para visualizar os produtos do carrinho
@app.route("/api/cart", methods = ["GET"])
@login_required #Declarando a autenticação obrigatória para acessar a rota
def view_cart(): #Função para recuperar os produtos do carrinho
    #User
    user = User.query.get(int(current_user.id)) #Variável que recupera o id do usuário
    cart_items = user.cart #Variável que recupera os itens do carrinho em uma lista
    cart_list = [] #Lista onde ficará cada item do carrinho
    #Laço for para recuperar cada item do carrinho
    for item in cart_items:
        product = Product.query.get(item.product_id) #Variável que recupera o id do produto
        cart_data = {
        "cart_product_id": item.id,
        "user_id" : item.user_id,
        "product_id" : item.product_id,
        "name_product" : product.name,
        "price_product" : product.price
        }
        cart_list.append(cart_data)
    return jsonify(cart_list) #Retorno da lista de produtos do carrinho

#Definindo a rota para finalizar a compra/CHECKOUT
@app.route("/api/cart/checkout", methods = ["POST"])
@login_required #Declarando a autenticação obrigatória para acessar a rota
def checkout(): #Função para finalizar a compra
    #User
    user = User.query.get(int(current_user.id)) #Variável que recupera o id do usuário
    cart_items = user.cart #Variável que recupera os itens do carrinho em uma lista
    total_price = 0 #Variável que armazena o preço total
    #Laço for para recuperar cada item do carrinho
    for item in cart_items:
        product = Product.query.get(item.product_id) #Variável que recupera o id do produto
        total_price += product.price #Somando o preço total
        db.session.delete(item) #Deletando o item do carrinho
    db.session.commit() #Efetuando as alterações no banco de dados
    return jsonify({"message" : f"Checkout successful. Cart has been cleared! Total price: R${total_price}"}), 200 #Retorno da função

#Definir a rota raíz(página inicial) e a função que será executada ao requisitar (Essa rota não é necessária para a aplicação)
@app.route("/")
def HelloWorld():
    return "Hello World!" #Retorno da função

#Verificando se o arquivo está sendo executado diretamente
if __name__ == "__main__":
    app.run(debug = True) #Modo depuração (corrigir erros e bugs no código-fonte)
    