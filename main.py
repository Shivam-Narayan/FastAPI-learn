from fastapi import  Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import session
from models import Product
from database import Session, engine
import database_models

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"]
)

database_models.Base.metadata.create_all(bind=engine)


@app.get("/")
def greet():
    return "Welcome to FastAPI"


products = [
    Product(id=1, name="phone", description="budget phone", price=99, quantity=10),
    Product(id=2, name="laptop", description="entry-level laptop", price=499, quantity=5),
    Product(id=3, name="headphones", description="wireless over-ear headphones", price=79, quantity=25),
    Product(id=4, name="smartwatch", description="fitness smartwatch", price=129, quantity=15),
    Product(id=5, name="tablet", description="compact android tablet", price=199, quantity=8),
    Product(id=6, name="charger", description="fast USB-C charger", price=29, quantity=40),
]

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()    

def init_db():
    db = Session()
    count = db.query(database_models.Product).count

    if count == 0:

        for product in products:
            db.add(database_models.Product(**product.model_dump()))

        db.commit()

init_db()

@app.get("/products")
def get_all_products(db: session = Depends(get_db)):
    db_products = db.query(database_models.Product).all()

    return db_products


@app.get("/products/{id}")
def get_product_by_id(id: int, db: session = Depends(get_db)):
    db_product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if db_product:
         return db_product
    return "product not found"


@app.post("/products")
def add_product(product: Product, db: session = Depends(get_db)):
    db.add(database_models.Product(**product.model_dump()))
    db.commit()
    return product


@app.put("/product/{id}")
def update_product(id: int, product: Product, db: session = Depends(get_db)):
    db_product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if db_product:
        db_product.name = product.name
        db_product.description = product.description
        db_product.price = product.price
        db_product.quantity = product.quantity
        db.commit()
        return "Product Updated"
    else: 
        return "No product found"


@app.delete("/product/{id}")
def delete_product(id: int, db: session = Depends(get_db)):
    db_product = db.query(database_models.Product).filter(database_models.Product.id == id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
    else:
        return "Product not found"
