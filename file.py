import streamlit as st
import pandas as pd
import mysql.connector
from PIL import Image
import random
import hashlib
import re
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
import requests
import time


class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=False
                )
            return self.connection
        except mysql.connector.Error as err:
            st.error(f"Database connection error: {err}")
            return None

    def get_cursor(self):
        conn = self.connect()
        if conn:
            try:
                return conn.cursor()
            except mysql.connector.Error as err:
                st.error(f"Cursor creation error: {err}")
                return None
        return None

    def commit(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.commit()
            except mysql.connector.Error as err:
                st.error(f"Commit error: {err}")
                self.connection.rollback()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()


try:
    db_manager = DatabaseManager(
        host="localhost",
        user="root",
        password="your database password",
        database="name database name as pharmacymanagement or any other ur wish"
    )
    
    if not db_manager.connect():
        st.error("Failed to connect to database. Please check your MySQL server and credentials.")
except Exception as e:
    st.error(f"Error initializing database: {str(e)}")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def email_valid(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def validate_phone(number):
    
    number = re.sub(r'[\s\-\(\)]', '', number)
    
    
    pattern = r'^(\+91|91|0)?[6-9]\d{9}$'
    return re.match(pattern, number) is not None and len(number) in [10, 11, 12, 13]

def validate_ssn(ssn):
    if not ssn:
        return True
    pattern = r"^\d{3}-\d{2}-\d{4}$"
    return re.match(pattern, ssn) is not None

def validate_bike_number(bike_number):
    
    indian_state_codes = [
        'AN', 'AP', 'AR', 'AS', 'BR', 'CH', 'CG', 'DD', 'DL', 'GA', 'GJ', 'HR', 'HP', 'JK', 'JH', 'KA', 'KL', 'LA', 'LD', 'MP', 'MH', 'MN', 'ML', 'MZ', 'NL', 'OD', 'PY', 'PB', 'RJ', 'SK', 'TN', 'TS', 'TR', 'UP', 'UK', 'WB'
    ]
    
    
    bike_number = bike_number.replace(' ', '').upper()
    

    state_code = bike_number[:2]
    if state_code not in indian_state_codes:
        st.error(f"Invalid state code. Please use one of: {', '.join(indian_state_codes)}")
        return False
    

    pattern = r'^[A-Z]{2}[A-Z]{2}\d{4}$'
    if not re.match(pattern, bike_number):
        st.error("Bike number should be in format: StateCode + Series + Number (e.g., TNKAAB1234)")
        return False
    
    return True


def create_tables():
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Insurance(
            InsuranceID INT PRIMARY KEY AUTO_INCREMENT,
            CompName VARCHAR(100) NOT NULL,
            Coverage DECIMAL(5,2) NOT NULL
        )''')

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Customers(
            C_Name VARCHAR(50) NOT NULL,
            C_Password VARCHAR(100) NOT NULL,
            C_Email VARCHAR(50) PRIMARY KEY NOT NULL,
            C_State VARCHAR(50) NOT NULL,
            C_Number VARCHAR(15) NOT NULL,
            C_SSN VARCHAR(20) UNIQUE,
            InsuranceID INT,
            FOREIGN KEY (InsuranceID) REFERENCES Insurance(InsuranceID) ON DELETE SET NULL
        )''')

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Drugs(
            D_Name VARCHAR(50) NOT NULL,
            D_ExpDate DATE NOT NULL,
            D_Use VARCHAR(50) NOT NULL,
            D_Qty INT NOT NULL,
            D_id INT PRIMARY KEY NOT NULL
        )''')

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Drug_Pricing(
            DrugID INT PRIMARY KEY,
            PricePerUnit DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (DrugID) REFERENCES Drugs(D_id) ON DELETE CASCADE
        )''')

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Prescription(
            PrespID INT PRIMARY KEY AUTO_INCREMENT,
            SSN VARCHAR(20),
            DocID INT NOT NULL,
            PrespDate DATE NOT NULL,
            FOREIGN KEY (SSN) REFERENCES Customers(C_SSN) ON DELETE CASCADE
        )''')

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Prescription_Drug(
            PrespID INT,
            DrugName VARCHAR(100) NOT NULL,
            PrespQty INT NOT NULL,
            RefillLimit INT NOT NULL,
            PRIMARY KEY (PrespID, DrugName),
            FOREIGN KEY (PrespID) REFERENCES Prescription(PrespID) ON DELETE CASCADE
        )''')

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Orders(
            O_Name VARCHAR(100) NOT NULL,
            O_Items VARCHAR(100) NOT NULL,
            O_Qty INT NOT NULL,
            O_id VARCHAR(100) PRIMARY KEY NOT NULL,
            Status VARCHAR(20) DEFAULT 'Placed',
            OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            StatusUpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            DeliveryAddress TEXT,
            PaymentMethod VARCHAR(50),
            ContactNumber VARCHAR(15),
            DeliveryAgentName VARCHAR(50),
            DeliveryAgentPhone VARCHAR(15),
            DeliveryAgentBike VARCHAR(20)
        )''')
        
        
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'DeliveryAgentName'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN DeliveryAgentName VARCHAR(50) AFTER ContactNumber")
            
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'DeliveryAgentPhone'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN DeliveryAgentPhone VARCHAR(15) AFTER DeliveryAgentName")
            
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'DeliveryAgentBike'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN DeliveryAgentBike VARCHAR(20) AFTER DeliveryAgentPhone")
            
    
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'StatusUpdateTime'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN StatusUpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER OrderDate")
        
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Billing(
            BillID INT PRIMARY KEY AUTO_INCREMENT,
            CustomerPhone VARCHAR(15) NOT NULL,
            BillDate DATETIME NOT NULL,
            TotalAmount DECIMAL(10,2) NOT NULL
        )''')

    
        cursor.execute('''CREATE TABLE IF NOT EXISTS Bill_Items(
            BillItemID INT PRIMARY KEY AUTO_INCREMENT,
            BillID INT NOT NULL,
            DrugID INT NOT NULL,
            DrugName VARCHAR(50) NOT NULL,
            Quantity INT NOT NULL,
            UnitPrice DECIMAL(10,2) NOT NULL,
            Subtotal DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (BillID) REFERENCES Billing(BillID) ON DELETE CASCADE,
            FOREIGN KEY (DrugID) REFERENCES Drugs(D_id) ON DELETE CASCADE
        )''')

        
        cursor.execute('''CREATE TABLE IF NOT EXISTS DeliveryAgents(
            DA_Name VARCHAR(50) NOT NULL,
            DA_Phone VARCHAR(15) PRIMARY KEY NOT NULL,
            DA_Password VARCHAR(100) NOT NULL,
            DA_Address TEXT NOT NULL,
            DA_BikeNumber VARCHAR(20),
            DA_Status VARCHAR(20) DEFAULT 'Available'
        )''')

        
        cursor.execute("SHOW COLUMNS FROM DeliveryAgents LIKE 'DA_BikeNumber'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE DeliveryAgents ADD COLUMN DA_BikeNumber VARCHAR(20) NOT NULL AFTER DA_Address")

        db_manager.commit()
        st.success("Tables created successfully!")

    except mysql.connector.Error as err:
        st.error(f"Error creating tables: {err}")
        db_manager.connection.rollback()

def initialize_sample_data():
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False

        
        cursor.execute("SELECT COUNT(*) FROM Insurance")
        count = cursor.fetchone()[0]
        
        if count == 0:
            
            insurances = [
                ("Blue Cross", 80.00),
                ("Aetna", 75.00),
                ("United Healthcare", 85.00),
                ("Medicare", 90.00)
            ]
            
            cursor.executemany("INSERT INTO Insurance (CompName, Coverage) VALUES (%s, %s)", insurances)
            db_manager.commit()
            return True
        return False
    except mysql.connector.Error as err:
        st.error(f"Error initializing sample data: {err}")
        return False


def customer_add_data(Cname, Cpass, Cemail, Cstate, Cnumber, Cssn=None, InsuranceID=None):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False

        
        cursor.execute("SELECT C_Email FROM Customers WHERE C_Email = %s", (Cemail,))
        if cursor.fetchone():
            st.error("Email already exists. Use a different one.")
            return False

        
        if not validate_phone(Cnumber):
            st.error("Please enter a valid phone number")
            return False
            
        if not validate_ssn(Cssn):
            st.error("SSN should be in format XXX-XX-XXXX")
            return False

        
        hashed_pass = hash_password(Cpass)

    
        cursor.execute('''INSERT INTO Customers(
            C_Name, C_Password, C_Email, C_State, C_Number, C_SSN, InsuranceID) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
            (Cname, hashed_pass, Cemail, Cstate, Cnumber, Cssn, InsuranceID))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return False

def customer_view_all_data():
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return []
        cursor.execute('SELECT * FROM Customers')
        return cursor.fetchall() or []
    except mysql.connector.Error as err:
        st.error(f"Error retrieving customer data: {err}")
        return []

# Drug functions
def drug_add_data(Dname, Dexpdate, Duse, Dqty, Did, price=None):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
        
        # Start transaction
        cursor.execute("START TRANSACTION")
        
        try:
            # Add drug to Drugs table
            cursor.execute('INSERT INTO Drugs VALUES (%s, %s, %s, %s, %s)', 
                         (Dname, Dexpdate, Duse, Dqty, Did))
            
            # Add pricing if provided
            if price is not None:
                cursor.execute('INSERT INTO Drug_Pricing VALUES (%s, %s)', (Did, price))
            
            # Commit transaction
            db_manager.commit()
            return True
            
        except mysql.connector.Error as err:
            # Rollback transaction on error
            db_manager.connection.rollback()
            st.error(f"Error adding drug: {err}")
            return False
            
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return False

def drug_view_all_data():
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return []
        cursor.execute('''SELECT d.D_Name, d.D_ExpDate, d.D_Use, d.D_Qty, d.D_id, dp.PricePerUnit 
                        FROM Drugs d
                        LEFT JOIN Drug_Pricing dp ON d.D_id = dp.DrugID''')
        return cursor.fetchall() or []
    except mysql.connector.Error as err:
        st.error(f"Error retrieving drug data: {err}")
        return []

def get_drug_price(drug_id):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return 0
        cursor.execute('SELECT PricePerUnit FROM Drug_Pricing WHERE DrugID = %s', (drug_id,))
        result = cursor.fetchone()
        return float(result[0]) if result and result[0] is not None else 0
    except mysql.connector.Error as err:
        st.error(f"Error getting drug price: {err}")
        return 0

def update_drug_price(drug_id, new_price):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
        cursor.execute('''INSERT INTO Drug_Pricing (DrugID, PricePerUnit) 
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE PricePerUnit = %s''',
                     (drug_id, new_price, new_price))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error updating drug price: {err}")
        return False

def drug_update(Duse, Did):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
            
        # Start transaction
        cursor.execute("START TRANSACTION")
        
        try:
            cursor.execute('UPDATE Drugs SET D_Use = %s WHERE D_id = %s', (Duse, Did))
            db_manager.commit()
            return True
            
        except mysql.connector.Error as err:
            # Rollback transaction on error
            db_manager.connection.rollback()
            st.error(f"Error updating drug: {err}")
            return False
            
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return False

def update_drug_quantity(drug_id, new_quantity):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
            
        # Start transaction
        cursor.execute("START TRANSACTION")
        
        try:
            # Check if drug exists
            cursor.execute('SELECT D_Name FROM Drugs WHERE D_id = %s', (drug_id,))
            drug = cursor.fetchone()
            if not drug:
                st.error("Drug not found")
                return False
                
            # Update quantity
            cursor.execute('UPDATE Drugs SET D_Qty = %s WHERE D_id = %s', (new_quantity, drug_id))
            db_manager.commit()
            return True
            
        except mysql.connector.Error as err:
            # Rollback transaction on error
            db_manager.connection.rollback()
            st.error(f"Error updating drug quantity: {err}")
            return False
            
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return False

def drug_delete(Did):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
        cursor.execute('DELETE FROM Drugs WHERE D_id = %s', (Did,))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error deleting drug: {err}")
        return False

# Order functions
# Modify the order_add_data function to fix the Status column issue
# Updated order_add_data function
def order_add_data(O_Name, O_Items, O_Qty, O_id, status="Placed", address="", payment_method="", contact_number=""):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
        
        # Check if order ID already exists
        cursor.execute('SELECT O_id FROM Orders WHERE O_id = %s', (O_id,))
        if cursor.fetchone():
            st.error("Order ID already exists. Please try again.")
            return False
        
        # Check if the Status column exists in the Orders table
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'Status'")
        status_column_exists = cursor.fetchone()
        
        if not status_column_exists:
            # Add the Status column if it doesn't exist
            cursor.execute("ALTER TABLE Orders ADD COLUMN Status VARCHAR(20) DEFAULT 'Placed'")
            db_manager.commit()
            
        # Check if other columns exist and add them if they don't
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'DeliveryAddress'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN DeliveryAddress TEXT")
            
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'ContactNumber'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN ContactNumber VARCHAR(15)")
            
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'PaymentMethod'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN PaymentMethod VARCHAR(50)")
            
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'OrderDate'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'StatusUpdateTime'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Orders ADD COLUMN StatusUpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            
        db_manager.commit()
        
        # Validate drug availability before inserting
        cursor.execute('SELECT D_Qty FROM Drugs WHERE D_Name = %s', (O_Items,))
        available_qty = cursor.fetchone()
        
        if not available_qty:
            st.error(f"Drug {O_Items} not found in inventory")
            return False
            
        if available_qty[0] < O_Qty:
            st.error(f"Not enough quantity available for {O_Items}. Available: {available_qty[0]}, Requested: {O_Qty}")
            return False
        
        # Now insert the order with all parameters
        cursor.execute('''INSERT INTO Orders (O_Name, O_Items, O_Qty, O_id, Status, DeliveryAddress, PaymentMethod, ContactNumber)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                     (O_Name, O_Items, O_Qty, O_id, status, address, payment_method, contact_number))
        
        # Update drug quantity
        cursor.execute('UPDATE Drugs SET D_Qty = D_Qty - %s WHERE D_Name = %s', (O_Qty, O_Items))
        db_manager.commit()
        return True
            
    except mysql.connector.Error as err:
        st.error(f"Error adding order: {err}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False

# Updated place order code for the shopping cart
def place_order_with_cart(username, cart, delivery_address, contact_number, payment_method):
    try:
        # Generate a unique order ID with timestamp and random component
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_component = random.randint(1000, 9999)
        base_order_id = f"{username}_{timestamp}_{random_component}"
        
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
            
        # Check if order ID already exists
        cursor.execute('SELECT O_id FROM Orders WHERE O_id LIKE %s', (f"{base_order_id}%",))
        if cursor.fetchone():
            # If ID exists, generate a new one with additional random component
            random_component = random.randint(10000, 99999)
            base_order_id = f"{username}_{timestamp}_{random_component}"
            
        # First check if all drugs are available in sufficient quantities
        for drug_id, item in cart.items():
            cursor.execute('SELECT D_Qty, D_Name FROM Drugs WHERE D_id = %s', (drug_id,))
            drug_info = cursor.fetchone()
            
            if not drug_info:
                st.error(f"Drug {item['name']} not found in inventory")
                return False
                
            available_qty = drug_info[0]
            if available_qty < item['quantity']:
                st.error(f"Not enough quantity available for {item['name']}. Available: {available_qty}, Requested: {item['quantity']}")
                return False
        
        # Create order records for each item in the cart
        for drug_id, item in cart.items():
            # Create unique order ID for each item
            order_id = f"{base_order_id}_{drug_id}"
            
            # Double check if this specific order ID exists
            cursor.execute('SELECT O_id FROM Orders WHERE O_id = %s', (order_id,))
            if cursor.fetchone():
                # If exists, generate a new unique ID
                order_id = f"{base_order_id}_{drug_id}_{random.randint(1000, 9999)}"
            
            try:
                # Start transaction
                cursor.execute("START TRANSACTION")
                
                # Insert order record
                cursor.execute('''
                    INSERT INTO Orders (O_id, O_Name, O_Items, O_Qty, Status, DeliveryAddress, PaymentMethod, ContactNumber)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (order_id, username, item['name'], item['quantity'], "Placed", delivery_address, payment_method, contact_number))
                
                # Update drug quantity
                cursor.execute('UPDATE Drugs SET D_Qty = D_Qty - %s WHERE D_id = %s', 
                             (item['quantity'], drug_id))
                
                # Commit transaction
                db_manager.commit()
                
            except mysql.connector.Error as err:
                # Rollback transaction on error
                db_manager.connection.rollback()
                st.error(f"Error processing order for {item['name']}: {err}")
                return False
        
        return {
            'success': True,
            'order_id': base_order_id,
            'items': [item['name'] for item in cart.values()],
            'total_qty': sum(item['quantity'] for item in cart.values()),
            'total_amount': sum(item['quantity'] * item['price'] for item in cart.values())
        }
            
    except Exception as e:
        st.error(f"Error placing order: {str(e)}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False
    
def order_view_all_data():
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return []
            
        # First check if StatusUpdateTime column exists
        cursor.execute("SHOW COLUMNS FROM Orders LIKE 'StatusUpdateTime'")
        has_status_time = cursor.fetchone() is not None
        
        if has_status_time:
            cursor.execute('''
                SELECT O_Name, O_Items, O_Qty, O_id, Status, 
                       DeliveryAddress, PaymentMethod, ContactNumber, OrderDate, StatusUpdateTime 
                FROM Orders
                ORDER BY OrderDate DESC
            ''')
        else:
            cursor.execute('''
                SELECT O_Name, O_Items, O_Qty, O_id, Status, 
                       DeliveryAddress, PaymentMethod, ContactNumber, OrderDate, OrderDate as StatusUpdateTime 
                FROM Orders
                ORDER BY OrderDate DESC
            ''')
        return cursor.fetchall() or []
    except mysql.connector.Error as err:
        st.error(f"Error retrieving order data: {err}")
        return []

def order_delete(Oid):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            st.error("Database connection error. Please try again later.")
            return False
            
        # Check if the order exists
        cursor.execute('SELECT Status FROM Orders WHERE O_id LIKE %s LIMIT 1', (f"{Oid}%",))
        existing_order = cursor.fetchone()
        if not existing_order:
            st.error(f"Order {Oid} not found")
            return False
            
        # Check if the order can be deleted (only allow deletion of Placed or Cancelled orders)
        if existing_order[0] not in ["Placed", "Cancelled"]:
            st.error(f"Cannot delete order with status: {existing_order[0]}. Only Placed or Cancelled orders can be deleted.")
            return False
            
        # Delete the order
        cursor.execute('DELETE FROM Orders WHERE O_id LIKE %s', (f"{Oid}%",))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False

def update_order_status(order_id, new_status, delivery_agent_phone=None):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            st.error("Database connection error. Please try again later.")
            return False
            
        # Validate the new status
        valid_statuses = ["Placed", "Confirmed", "Shipped", "Delivered", "Cancelled"]
        if new_status not in valid_statuses:
            st.error(f"Invalid status: {new_status}. Must be one of {', '.join(valid_statuses)}")
            return False
            
        # Check if the order exists
        cursor.execute('SELECT Status FROM Orders WHERE O_id LIKE %s LIMIT 1', (f"{order_id}%",))
        existing_order = cursor.fetchone()
        if not existing_order:
            st.error(f"Order {order_id} not found")
            return False
            
        current_status = existing_order[0]
        
        # Validate status transition
        valid_transitions = {
            "Placed": ["Confirmed", "Cancelled"],
            "Confirmed": ["Shipped", "Cancelled"],
            "Shipped": ["Delivered", "Cancelled"],
            "Delivered": [],  # No further transitions allowed
            "Cancelled": []   # No further transitions allowed
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            st.error(f"Cannot change status from {current_status} to {new_status}")
            return False
            
        # Get delivery agent information if provided
        delivery_agent_info = None
        if delivery_agent_phone:
            cursor.execute('SELECT DA_Name, DA_Phone, DA_BikeNumber FROM DeliveryAgents WHERE DA_Phone = %s', (delivery_agent_phone,))
            delivery_agent_info = cursor.fetchone()
            if not delivery_agent_info:
                st.error("Delivery agent not found")
                return False
            
        # Update all order items with the same base order ID
        if delivery_agent_info and new_status == "Shipped":
            cursor.execute('''
                UPDATE Orders 
                SET Status = %s, 
                    DeliveryAgentName = %s, 
                    DeliveryAgentPhone = %s, 
                    DeliveryAgentBike = %s,
                    StatusUpdateTime = CURRENT_TIMESTAMP
                WHERE O_id LIKE %s
            ''', (new_status, delivery_agent_info[0], delivery_agent_info[1], delivery_agent_info[2], f"{order_id}%"))
        else:
            cursor.execute('''
                UPDATE Orders 
                SET Status = %s,
                    StatusUpdateTime = CURRENT_TIMESTAMP
                WHERE O_id LIKE %s
            ''', (new_status, f"{order_id}%"))
            
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False

def create_bill(customer_phone, bill_items):
    try:
        cursor = db_manager.get_cursor()
        if cursor:
            # Calculate total amount
            total_amount = 0
            for item in bill_items:
                drug_name = item['name']
                quantity = item['quantity']
                cursor.execute('''
                    SELECT PricePerUnit 
                    FROM Drug_Pricing dp 
                    JOIN Drugs d ON dp.DrugID = d.D_id 
                    WHERE d.D_Name = %s
                ''', (drug_name,))
                price = cursor.fetchone()
                if price:
                    total_amount += price[0] * quantity

            # Insert bill
            cursor.execute('''INSERT INTO Billing (CustomerPhone, BillDate, TotalAmount)
                            VALUES (%s, NOW(), %s)''', (customer_phone, total_amount))
            db_manager.commit()
            return True
    except mysql.connector.Error as err:
        st.error(f"Error creating bill: {err}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return False

def view_bills(customer_phone=None):
    try:
        cursor = db_manager.get_cursor()
        if cursor:
            if customer_phone:
                cursor.execute('''
                    SELECT b.BillID, b.CustomerPhone, b.BillDate, b.TotalAmount
                    FROM Billing b
                    WHERE b.CustomerPhone = %s
                    ORDER BY b.BillDate DESC
                ''', (customer_phone,))
            else:
                cursor.execute('''
                    SELECT b.BillID, b.CustomerPhone, b.BillDate, b.TotalAmount
                    FROM Billing b
                    ORDER BY b.BillDate DESC
                ''')
            return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"Error viewing bills: {err}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return []

# Prescription functions
def add_prescription(ssn, doctor_id, drugs_and_qtys):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return None

        cursor.execute('''INSERT INTO Prescription (SSN, DocID, PrespDate) 
                        VALUES (%s, %s, %s)''', 
                     (ssn, doctor_id, datetime.now().date()))
        db_manager.commit()

        presp_id = cursor.lastrowid

        for drug_name, qty, refills in drugs_and_qtys:
            cursor.execute('''INSERT INTO Prescription_Drug 
                           (PrespID, DrugName, PrespQty, RefillLimit) 
                           VALUES (%s, %s, %s, %s)''', 
                         (presp_id, drug_name, qty, refills))
        db_manager.commit()
        return presp_id
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return None

def view_prescriptions(ssn=None):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return []

        if ssn:
            cursor.execute('''SELECT p.PrespID, p.DocID, p.PrespDate
                            FROM Prescription p
                            WHERE p.SSN = %s''', (ssn,))
            prescriptions = cursor.fetchall()
            result = []
            for p in prescriptions:
                cursor.execute('''SELECT DrugName, PrespQty, RefillLimit 
                                FROM Prescription_Drug 
                                WHERE PrespID = %s''', (p[0],))
                drugs = cursor.fetchall()
                drug_details = []
                for drug in drugs:
                    drug_details.append(f"{drug[0]} ({drug[1]} tablets, {drug[2]} refills)")
                result.append((p[0], p[1], p[2], ", ".join(drug_details)))
            return result
        else:
            cursor.execute('SELECT PrespID, SSN, DocID, PrespDate FROM Prescription')
            prescriptions = cursor.fetchall()
            result = []
            for p in prescriptions:
                cursor.execute('''SELECT DrugName, PrespQty, RefillLimit 
                                FROM Prescription_Drug 
                                WHERE PrespID = %s''', (p[0],))
                drugs = cursor.fetchall()
                drug_details = []
                for drug in drugs:
                    drug_details.append(f"{drug[0]} ({drug[1]} tablets, {drug[2]} refills)")
                result.append((p[0], p[1], p[2], p[3], ", ".join(drug_details)))
            return result
    except mysql.connector.Error as err:
        st.error(f"Error retrieving prescriptions: {err}")
        return []

# Authentication
def get_authenticate(username, password):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
        cursor.execute('SELECT C_Password FROM Customers WHERE C_Name = %s', (username,))
        cust_password = cursor.fetchone()
        if cust_password:
            hashed_input_pass = hash_password(password)
            return cust_password[0] == hashed_input_pass
        return False
    except mysql.connector.Error as err:
        st.error(f"Authentication error: {err}")
        return False

def update_customer_profile(username, ssn=None, insurance_id=None):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False

        updates = []
        values = []

        if ssn:
            if not validate_ssn(ssn):
                st.error("SSN should be in format XXX-XX-XXXX")
                return False
            updates.append("C_SSN = %s")
            values.append(ssn)

        if insurance_id is not None:
            updates.append("InsuranceID = %s")
            values.append(insurance_id)

        if not updates:
            return False

        query = f"UPDATE Customers SET {', '.join(updates)} WHERE C_Name = %s"
        values.append(username)

        cursor.execute(query, tuple(values))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error updating profile: {err}")
        return False

# Customer Dashboard
def customer_dashboard(username):
    # Initialize session state for cart
    if 'cart' not in st.session_state:
        st.session_state.cart = {}
    if 'show_checkout' not in st.session_state:
        st.session_state.show_checkout = False
    if 'order_confirmed' not in st.session_state:
        st.session_state.order_confirmed = False
    
    st.title(f"👋 Welcome, {username}!")
    
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return

        # Get customer details including phone number
        cursor.execute('SELECT C_Email, C_SSN, InsuranceID, C_Number FROM Customers WHERE C_Name = %s', (username,))
        customer = cursor.fetchone()
        if not customer:
            st.error("Customer information not found")
            return
            
        # Store customer phone number in session state if not already there
        if 'customer_phone' not in st.session_state:
            st.session_state.customer_phone = customer[3] if customer[3] else ""
            
    except mysql.connector.Error as err:
        st.error(f"Error retrieving customer info: {err}")
        return

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Orders", "💊 Prescriptions", "🛍️ Shop", "👤 Profile"])

    # Orders Tab
    with tab1:
        st.subheader("Your Orders")
        # Add order status filter
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Placed", "Confirmed", "Shipped", "Delivered", "Cancelled"],
            key="order_status_filter"
        )
        
        order_data = order_view_all_data()
        filtered_orders = [order for order in order_data if order[0] == username]
        
        if filtered_orders:
            # Group orders by base order ID
            grouped_orders = {}
            for order in filtered_orders:
                if len(order) <= 4:
                    continue
                    
                order_name = order[0]
                item_name = order[1]
                quantity = order[2]
                order_id = order[3]
                status = order[4] if len(order) > 4 else "Placed"
                address = order[5] if len(order) > 5 else ""
                payment = order[6] if len(order) > 6 else ""
                contact = order[7] if len(order) > 7 else ""
                
                # Extract base order ID (removing the drug ID suffix)
                order_id_parts = order_id.split('_')
                base_order_id = '_'.join(order_id_parts[:-1]) if len(order_id_parts) > 2 else order_id
                
                if status_filter != "All" and status != status_filter:
                    continue
                    
                item_price = 0
                try:
                    cursor = db_manager.get_cursor()
                    if cursor:
                        cursor.execute('SELECT D_id FROM Drugs WHERE D_Name = %s', (item_name,))
                        drug_id = cursor.fetchone()
                        if drug_id:
                            item_price = get_drug_price(drug_id[0])
                except:
                    pass
                    
                if base_order_id not in grouped_orders:
                    grouped_orders[base_order_id] = {
                        'items': [],
                        'status': status,
                        'address': address,
                        'payment': payment,
                        'contact': contact,
                        'date': order[8] if len(order) > 8 else "Unknown date",
                        'status_update_time': order[9] if len(order) > 9 else "Unknown",
                        'total': 0
                    }
                    
                grouped_orders[base_order_id]['items'].append({
                    'name': item_name,
                    'quantity': quantity,
                    'price': item_price,
                    'subtotal': item_price * quantity
                })
                grouped_orders[base_order_id]['total'] += item_price * quantity
                
            # Display grouped orders
            for base_order_id, order_info in grouped_orders.items():
                with st.expander(f"Order #{base_order_id}"):
                    st.write(f"**Status:** {order_info['status']}")
                    st.write(f"**Date:** {order_info['date']}")
                    
                    if order_info['status'] in ["Shipped", "Delivered"]:
                        try:
                            cursor = db_manager.get_cursor()
                            if cursor:
                                cursor.execute('''
                                    SELECT DeliveryAgentName, DeliveryAgentPhone, DeliveryAgentBike 
                                    FROM Orders 
                                    WHERE O_id LIKE %s LIMIT 1
                                ''', (f"{base_order_id}%",))
                                agent_info = cursor.fetchone()
                                if agent_info:
                                    st.write("**Delivery Agent Information:**")
                                    st.write(f"Name: {agent_info[0]}")
                                    st.write(f"Phone: {agent_info[1]}")
                                    st.write(f"Bike Number: {agent_info[2]}")
                        except mysql.connector.Error as err:
                            st.error(f"Error retrieving delivery agent information: {err}")
                    
                    st.write("**Items:**")
                    for item in order_info['items']:
                        st.write(f"• {item['name']} (Qty: {item['quantity']}) - ₹{item['price']:.2f} × {item['quantity']} = ₹{item['subtotal']:.2f}")
                    
                    st.write(f"**Total Amount:** ₹{order_info['total']:.2f}")
                    if order_info['address']:
                        st.write(f"**Delivery Address:** {order_info['address']}")
                    if order_info['contact']:
                        st.write(f"**Contact Number:** {order_info['contact']}")
                    if order_info['payment']:
                        st.write(f"**Payment Method:** {order_info['payment']}")
                    
                    if st.button("🔄 Refresh Order Status", key=f"refresh_{base_order_id}"):
                        st.rerun()
        else:
            st.info("No orders found")

    # Prescriptions Tab
    with tab2:
        st.subheader("Your Prescriptions")
        if customer and customer[1]:  # If customer has SSN
            try:
                # View existing prescriptions
                prescriptions = view_prescriptions(customer[1])
                if prescriptions:
                    for presc in prescriptions:
                        with st.expander(f"Prescription #{presc[0]} - {presc[3]}"):
                            st.write(f"**Doctor ID:** {presc[1]}")
                            st.write(f"**Date:** {presc[3]}")
                            st.write(f"**Drugs:** {presc[2]}")
                else:
                    st.info("No prescriptions found.")
            except mysql.connector.Error as err:
                st.error(f"Error retrieving prescriptions: {err}")

            # Add new prescription section
            st.markdown("### Add New Prescription")
            cursor = db_manager.get_cursor()
            if cursor:
                try:
                    cursor.execute('SELECT D_Name FROM Drugs')
                    available_drugs = [drug[0] for drug in cursor.fetchall()]
                    
                    st.markdown("**Add your prescription medicines:**")
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        selected_drug = st.selectbox("Select Medicine", available_drugs, key="drug_select")
                    with col2:
                        quantity = st.number_input("Quantity", min_value=1, value=1, key="drug_qty")
                    with col3:
                        refills = st.number_input("Refills", min_value=0, value=1, key="drug_refills")
                    
                    if 'selected_medicines' not in st.session_state:
                        st.session_state.selected_medicines = []
                    
                    if st.button("Add Medicine", key="add_medicine"):
                        new_medicine = {
                            'name': selected_drug,
                            'quantity': quantity,
                            'refills': refills
                        }
                        st.session_state.selected_medicines.append(new_medicine)
                        st.rerun()
                    
                    if st.session_state.selected_medicines:
                        st.markdown("**Selected Medicines:**")
                        for i, med in enumerate(st.session_state.selected_medicines):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"• {med['name']} - {med['quantity']} tablets, {med['refills']} refills")
                            with col2:
                                if st.button("Remove", key=f"remove_{i}"):
                                    st.session_state.selected_medicines.pop(i)
                                    st.rerun()
                    
                    with st.form("add_prescription_form"):
                        doctor_id = st.text_input("Doctor ID", key="doctor_id")
                        submitted = st.form_submit_button("Add Prescription")
                        
                        if submitted:
                            if not doctor_id:
                                st.error("Please enter your Doctor ID")
                            elif not st.session_state.selected_medicines:
                                st.error("Please add at least one medicine")
                            else:
                                try:
                                    drugs_and_qtys = []
                                    for med in st.session_state.selected_medicines:
                                        drugs_and_qtys.append((
                                            med['name'],
                                            med['quantity'],
                                            med['refills']
                                        ))
                                    
                                    if add_prescription(customer[1], doctor_id, drugs_and_qtys):
                                        st.success("Prescription added successfully!")
                                        st.session_state.selected_medicines = []
                                        st.rerun()
                                    else:
                                        st.error("Failed to add prescription. Please try again.")
                                except Exception as e:
                                    st.error(f"Error adding prescription: {str(e)}")
                except mysql.connector.Error as err:
                    st.error(f"Error loading medicines: {err}")
        else:
            st.info("No prescriptions available. Please add your SSN to view prescriptions.")

    # Shop Tab
    with tab3:
        st.subheader("Available Medicines")
        drugs = drug_view_all_data()
        
        if drugs:
            # Search functionality
            search_term = st.text_input("Search medicines", key="drug_search")
            filtered_drugs = [drug for drug in drugs if search_term.lower() in drug[0].lower()]
            
            if filtered_drugs:
                for drug in filtered_drugs:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{drug[0]}**")
                        st.write(f"Use: {drug[2]}")
                        price = float(drug[5]) if drug[5] is not None else 0
                        st.write(f"Price: ₹{price:.2f}")
                    with col2:
                        st.write(f"Available: {drug[3]}")
                    with col3:
                        # Get current quantity from cart
                        current_qty = st.session_state.cart.get(drug[4], {}).get('quantity', 0)
                        
                        # Quantity controls
                        qty_col1, qty_col2, qty_col3 = st.columns([1, 2, 1])
                        with qty_col1:
                            if st.button("➖", key=f"shop_minus_{drug[4]}"):
                                if drug[4] in st.session_state.cart:
                                    if st.session_state.cart[drug[4]]['quantity'] > 1:
                                        st.session_state.cart[drug[4]]['quantity'] -= 1
                                    else:
                                        del st.session_state.cart[drug[4]]
                                    st.rerun()
                        with qty_col2:
                            st.write(f"{current_qty}")
                        with qty_col3:
                            if st.button("➕", key=f"shop_plus_{drug[4]}"):
                                if drug[3] > current_qty:  # Check if stock available
                                    if drug[4] not in st.session_state.cart:
                                        st.session_state.cart[drug[4]] = {
                                            'name': drug[0],
                                            'quantity': 1,
                                            'price': price
                                        }
                                    else:
                                        st.session_state.cart[drug[4]]['quantity'] += 1
                                    st.rerun()
                                else:
                                    st.warning("Not enough stock available")
            else:
                st.info("No medicines found matching your search.")
        else:
            st.info("No medicines available in the shop.")
            
        # Cart sidebar
        with st.sidebar:
            if st.session_state.cart:
                st.subheader("Your Cart")
                total = 0
                total_qty = 0
                
                for drug_id, item in st.session_state.cart.items():
                    st.write(f"**{item['name']}**")
                    st.write(f"Qty: {item['quantity']} × ₹{item['price']:.2f} = ₹{item['quantity']*item['price']:.2f}")
                    total += item['quantity'] * item['price']
                    total_qty += item['quantity']
                    
                    if st.button(f"Remove {item['name']}", key=f"remove_{drug_id}"):
                        del st.session_state.cart[drug_id]
                        st.rerun()
                    st.divider()
                
                st.write(f"**Total Items:** {total_qty}")
                st.write(f"**Total Amount:** ₹{total:.2f}")
                
                if st.button("Proceed to Checkout", key="checkout"):
                    st.session_state.show_checkout = True
                    st.rerun()
            else:
                st.write("Your cart is empty")

        # Checkout page
        if st.session_state.show_checkout and st.session_state.cart:
            st.markdown('<div id="order-summary"></div>', unsafe_allow_html=True)
            st.subheader("Order Summary")
            
            total = 0
            total_qty = 0
            order_items = []
            
            for drug_id, item in st.session_state.cart.items():
                order_items.append({
                    'Drug': item['name'],
                    'Quantity': item['quantity'],
                    'Unit Price': f"₹{item['price']:.2f}",
                    'Subtotal': f"₹{item['quantity']*item['price']:.2f}"
                })
                total += item['quantity'] * item['price']
                total_qty += item['quantity']
            
            st.dataframe(pd.DataFrame(order_items))
            st.write(f"**Total Quantity:** {total_qty}")
            st.write(f"**Total Amount:** ₹{total:.2f}")
            
            st.subheader("Payment Method")
            payment_method = st.radio(
                "Select payment method",
                ["Cash on Delivery", "Credit/Debit Card", "UPI", "Net Banking"],
                key="payment_method"
            )
            
            phone = st.text_input("Contact Number", value=st.session_state.customer_phone, key="contact_number")
            delivery_address = st.text_area("Delivery Address", key="delivery_address")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Place Order", key="place_order"):
                    if not phone:
                        st.error("Please provide contact number")
                    elif not delivery_address:
                        st.error("Please provide delivery address")
                    else:
                        st.session_state.customer_phone = phone
                        
                        order_result = place_order_with_cart(username, st.session_state.cart, 
                                                          delivery_address, phone, payment_method)
                        
                        if order_result and order_result['success']:
                            st.session_state.order_confirmed = True
                            
                            # Create bill using cart items before clearing cart
                            bill_items = []
                            for drug_id, item in st.session_state.cart.items():
                                bill_items.append({
                                    'drug_id': drug_id,
                                    'drug_name': item['name'],
                                    'quantity': item['quantity'],
                                    'unit_price': item['price'],
                                    'subtotal': item['quantity'] * item['price']
                                })
                            
                            # Clear cart after successful order
                            st.session_state.cart = {}
                            st.session_state.show_checkout = False
                            
                            st.success(f"Order placed successfully! Order ID: {order_result['order_id']}")
                            st.write(f"Items: {', '.join(order_result['items'])}")
                            st.write(f"Total Items: {order_result['total_qty']}")
                            st.write(f"Total Amount: ₹{order_result['total_amount']:.2f}")
                            
                            # Create bill
                            bill_id = create_bill(phone, bill_items)
                            if bill_id:
                                st.success(f"Bill #{bill_id} generated successfully!")
                            
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Failed to place order. Please check inventory or try again.")
            
            with col2:
                if st.button("Back to Cart", key="back_to_cart"):
                    st.session_state.show_checkout = False
                    st.rerun()

    # Profile Tab
    with tab4:
        st.subheader("Your Profile")
        
        # Display current profile information
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Personal Information")
            st.write(f"**Name:** {username}")
            st.write(f"**Email:** {customer[0]}")
            st.write(f"**Phone:** {customer[3]}")
            
            # Display insurance information if available
            if customer[2]:
                try:
                    cursor = db_manager.get_cursor()
                    if cursor:
                        cursor.execute('SELECT CompName FROM Insurance WHERE InsuranceID = %s', (customer[2],))
                        insurance = cursor.fetchone()
                        if insurance:
                            st.write(f"**Insurance Provider:** {insurance[0]}")
                            st.write(f"**Insurance ID:** {customer[2]}")
                except mysql.connector.Error as err:
                    st.error(f"Error retrieving insurance information: {err}")
            
            # Display SSN if available
            if customer[1]:
                st.write(f"**SSN:** {customer[1]}")
        
        with col2:
            st.markdown("### Order Statistics")
            try:
                cursor = db_manager.get_cursor()
                if cursor:
                    # Get total orders
                    cursor.execute('''
                        SELECT COUNT(DISTINCT O_id) 
                        FROM Orders 
                        WHERE O_Name = %s
                    ''', (username,))
                    total_orders = cursor.fetchone()[0]
                    
                    # Get total spent
                    cursor.execute('''
                        SELECT SUM(O_Qty * (
                            SELECT PricePerUnit 
                            FROM Drug_Pricing dp 
                            JOIN Drugs d ON dp.DrugID = d.D_id 
                            WHERE d.D_Name = O_Items
                        ))
                        FROM Orders 
                        WHERE O_Name = %s
                    ''', (username,))
                    total_spent = cursor.fetchone()[0] or 0
                    
                    st.write(f"**Total Orders:** {total_orders}")
                    st.write(f"**Total Spent:** ₹{total_spent:.2f}")
            except mysql.connector.Error as err:
                st.error(f"Error retrieving order statistics: {err}")
        
        # Orders Section
        st.markdown("### Your Orders")
        try:
            cursor = db_manager.get_cursor()
            if cursor:
                # Get all delivered orders
                cursor.execute('''
                    SELECT O_id, O_Items, O_Qty, Status, OrderDate, DeliveryAddress, PaymentMethod, ContactNumber
                    FROM Orders 
                    WHERE O_Name = %s AND Status = 'Delivered'
                    ORDER BY OrderDate DESC
                ''', (username,))
                orders = cursor.fetchall()
                
                if orders:
                    # Group orders by base order ID
                    grouped_orders = {}
                    for order in orders:
                        order_id = order[0]
                        item_name = order[1]
                        quantity = order[2]
                        status = order[3]
                        date = order[4]
                        address = order[5] if len(order) > 5 else ""
                        payment = order[6] if len(order) > 6 else ""
                        contact = order[7] if len(order) > 7 else ""
                        
                        # Extract base order ID (removing the drug ID suffix)
                        order_id_parts = order_id.split('_')
                        base_order_id = '_'.join(order_id_parts[:-1]) if len(order_id_parts) > 2 else order_id
                        
                        if base_order_id not in grouped_orders:
                            grouped_orders[base_order_id] = {
                                'items': [],
                                'status': status,
                                'date': date,
                                'address': address,
                                'payment': payment,
                                'contact': contact,
                                'total': 0
                            }
                        
                        # Get drug price
                        price = 0
                        try:
                            cursor.execute('SELECT D_id FROM Drugs WHERE D_Name = %s', (item_name,))
                            drug_id = cursor.fetchone()
                            if drug_id:
                                price = get_drug_price(drug_id[0])
                        except:
                            pass
                        
                        grouped_orders[base_order_id]['items'].append({
                            'name': item_name,
                            'quantity': quantity,
                            'price': price,
                            'subtotal': price * quantity
                        })
                        grouped_orders[base_order_id]['total'] += price * quantity
                    
                    # Display orders
                    for order_id, order_info in grouped_orders.items():
                        with st.expander(f"Order #{order_id}"):
                            st.write(f"**Status:** {order_info['status']}")
                            st.write(f"**Date:** {order_info['date']}")
                            
                            # Display items
                            st.write("**Items:**")
                            for item in order_info['items']:
                                st.write(f"• {item['name']} (Qty: {item['quantity']}) - ₹{item['price']:.2f} × {item['quantity']} = ₹{item['subtotal']:.2f}")
                            
                            st.write(f"**Total Amount:** ₹{order_info['total']:.2f}")
                            if order_info['address']:
                                st.write(f"**Delivery Address:** {order_info['address']}")
                            if order_info['contact']:
                                st.write(f"**Contact Number:** {order_info['contact']}")
                            if order_info['payment']:
                                st.write(f"**Payment Method:** {order_info['payment']}")
                else:
                    st.info("No delivered orders found.")
        except mysql.connector.Error as err:
            st.error(f"Error retrieving orders: {err}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
        
        # Prescriptions Section
        st.markdown("### Your Prescriptions")
        if customer[1]:  # If customer has SSN
            try:
                prescriptions = view_prescriptions(customer[1])
                if prescriptions:
                    for presc in prescriptions:
                        with st.expander(f"Prescription #{presc[0]} - {presc[3]}"):
                            st.write(f"**Doctor ID:** {presc[1]}")
                            st.write(f"**Date:** {presc[3]}")
                            st.write(f"**Drugs:** {presc[2]}")
                else:
                    st.info("No prescriptions found.")
            except mysql.connector.Error as err:
                st.error(f"Error retrieving prescriptions: {err}")
        else:
            st.info("No prescriptions available. Please add your SSN to view prescriptions.")
        
        # Update profile section
        st.markdown("### Update Profile")
        with st.form("update_profile_form"):
            ssn = st.text_input("SSN", value=customer[1] if customer[1] else "", key="ssn_input")
            
            # Insurance selection
            try:
                cursor = db_manager.get_cursor()
                if cursor:
                    cursor.execute('SELECT InsuranceID, CompName FROM Insurance')
                    insurances = cursor.fetchall()
                    insurance_options = ["None"] + [f"{ins[0]} - {ins[1]}" for ins in insurances]
                    
                    # Get current insurance
                    current_insurance = "None"
                    if customer[2]:  # If customer has insurance
                        cursor.execute('SELECT CompName FROM Insurance WHERE InsuranceID = %s', (customer[2],))
                        result = cursor.fetchone()
                        if result:
                            current_insurance = f"{customer[2]} - {result[0]}"
                    
                    selected_insurance = st.selectbox(
                        "Insurance Provider",
                        insurance_options,
                        index=insurance_options.index(current_insurance) if current_insurance in insurance_options else 0
                    )
                    
                    # Extract insurance ID if selected
                    insurance_id = None
                    if selected_insurance != "None":
                        insurance_id = int(selected_insurance.split(" - ")[0])
                    
                    submitted = st.form_submit_button("Update Profile")
                    if submitted:
                        try:
                            cursor = db_manager.get_cursor()
                            if cursor:
                                cursor.execute('''UPDATE Customers 
                                                SET C_SSN = %s, InsuranceID = %s 
                                                WHERE C_Email = %s''',
                                             (ssn, insurance_id, customer[0]))
                                db_manager.commit()
                                st.success("Profile updated successfully!")
                                st.rerun()
                        except mysql.connector.Error as err:
                            st.error(f"Error updating profile: {err}")
            except mysql.connector.Error as err:
                st.error(f"Error loading insurance options: {err}")

# Admin Panel
def admin_panel():
    st.title("Pharmacy Admin Panel")
    
    # Initialize session state for admin choice if not exists
    if 'admin_choice' not in st.session_state:
        st.session_state.admin_choice = None
    
    # Sidebar navigation
    admin_choice = st.sidebar.radio("Menu", ["Drugs", "Customers", "Orders", "Prescriptions", "Insurance", "Billing", "Pharmacy Performance", "Delivery Agents"])
    
    # Clear previous content
    st.empty()
    
    if admin_choice == "Drugs":
        st.header("Drug Management")
        action = st.radio("Actions", ["Add", "View", "Update", "Delete", "Low Stock"])
        
        if action == "Add":
            with st.form("add_drug_form"):
                drug_name = st.text_input("Drug Name")
                exp_date = st.date_input("Expiry Date")
                drug_use = st.text_area("Usage Instructions")
                quantity = st.number_input("Quantity", min_value=0)
                drug_id = st.text_input("Drug ID")
                price = st.number_input("Price per Unit", min_value=0.0, step=0.1)
                
                submitted = st.form_submit_button("Add Drug")
                if submitted:
                    if drug_name and exp_date and drug_use and quantity and drug_id:
                        drug_add_data(drug_name, exp_date, drug_use, quantity, drug_id, price)
                        st.success("Drug added successfully")
                    else:
                        st.warning("Please fill all required fields")
        
        elif action == "View":
            drugs = drug_view_all_data()
            if drugs:
                st.write(pd.DataFrame(drugs, columns=["Name", "Expiry Date", "Usage", "Quantity", "ID", "Price"]))
            else:
                st.info("No drugs found")
        
        elif action == "Update":
            st.subheader("Update Drug")
            drugs = drug_view_all_data()
            if drugs:
                # First, let user enter drug ID and show current values
                drug_id = st.text_input("Enter Drug ID to Update")
                
                if drug_id:
                    try:
                        # Convert drug_id to string for comparison
                        drug_id = str(drug_id).strip()
                        
                        # Find the drug with the entered ID
                        selected_drug = None
                        for drug in drugs:
                            if str(drug[4]).strip() == drug_id:  # Convert drug ID to string for comparison
                                selected_drug = drug
                                break
                        
                        if selected_drug:
                            # Get current values
                            current_use = selected_drug[2]  # Usage is at index 2
                            current_price = selected_drug[5] if len(selected_drug) > 5 else None  # Price is at index 5
                            
                            # Show current drug information
                            st.write(f"**Drug Name:** {selected_drug[0]}")
                            st.write("**Current Price:**", f"₹{current_price:.2f}" if current_price else "Not set")
                            st.write("**Current Usage:**", current_use)
                            
                            # Create a form for updates
                            with st.form(key="update_drug_form"):
                                # Create two columns for price and usage updates
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    new_price = st.number_input("New Price (Optional)", 
                                                              min_value=0.0, 
                                                              step=0.1,
                                                              value=float(current_price) if current_price else 0.0)
                                
                                with col2:
                                    new_use = st.text_area("New Usage Instructions (Optional)", 
                                                         value=current_use)
                                
                                # Add a note about optional updates
                                st.info("💡 You can update either price or usage, or both. Leave unchanged if no update needed.")
                                
                                # Submit button
                                submitted = st.form_submit_button("Update Drug")
                                
                                if submitted:
                                    try:
                                        # Update usage if changed and not empty
                                        if new_use and new_use != current_use:
                                            drug_update(new_use, drug_id)
                                        
                                        # Update price if changed and not zero
                                        if new_price > 0 and new_price != current_price:
                                            update_drug_price(drug_id, new_price)
                                        
                                        st.success("Drug updated successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating drug: {str(e)}")
                        else:
                            st.error("❌ Drug ID not found. Please enter a valid Drug ID.")
                            # Show available drug IDs for reference
                            st.write("Available Drug IDs:")
                            drug_list = [(drug[0], drug[4]) for drug in drugs]  # (name, id)
                            st.write(pd.DataFrame(drug_list, columns=['Drug Name', 'Drug ID']))
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.info("No drugs found")
        
        elif action == "Delete":
            st.subheader("Delete Drug")
            drugs = drug_view_all_data()
            if drugs:
                # First, let user enter drug ID and show information
                drug_id = st.text_input("Enter Drug ID to Delete")
                
                if drug_id:
                    try:
                        # Convert drug_id to string for comparison
                        drug_id = str(drug_id).strip()
                        
                        # Find the drug with the entered ID
                        selected_drug = None
                        for drug in drugs:
                            if str(drug[4]).strip() == drug_id:  # Convert drug ID to string for comparison
                                selected_drug = drug
                                break
                        
                        if selected_drug:
                            # Get current values
                            current_use = selected_drug[2]  # Usage is at index 2
                            current_price = selected_drug[5] if len(selected_drug) > 5 else None  # Price is at index 5
                            
                            # Show drug information
                            st.warning("⚠️ Please review the drug information before deletion:")
                            st.write(f"**Drug Name:** {selected_drug[0]}")
                            st.write("**Current Price:**", f"₹{current_price:.2f}" if current_price else "Not set")
                            st.write("**Current Usage:**", current_use)
                            st.write("**Current Stock:**", selected_drug[3])  # Quantity is at index 3
                            
                            # Create a form for deletion confirmation
                            with st.form(key="delete_drug_form"):
                                # Add warning message
                                st.error("⚠️ Warning: This action cannot be undone!")
                                
                                # Confirmation checkbox
                                confirm_delete = st.checkbox("I understand this will permanently delete the drug and related records")
                                
                                # Submit button
                                submitted = st.form_submit_button("Delete Drug")
                                
                                if submitted:
                                    if confirm_delete:
                                        try:
                                            if drug_delete(drug_id):
                                                st.success("Drug deleted successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete drug. Please try again.")
                                        except Exception as e:
                                            st.error(f"Error deleting drug: {str(e)}")
                                    else:
                                        st.error("Please confirm deletion by checking the checkbox")
                        else:
                            st.error("❌ Drug ID not found. Please enter a valid Drug ID.")
                            # Show available drug IDs for reference
                            st.write("Available Drug IDs:")
                            drug_list = [(drug[0], drug[4]) for drug in drugs]  # (name, id)
                            st.write(pd.DataFrame(drug_list, columns=['Drug Name', 'Drug ID']))
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.info("No drugs found")
        
        elif action == "Low Stock":
            st.subheader("Low Stock Drugs")
            drugs = drug_view_all_data()
            if drugs:
                # Filter drugs with quantity less than 50
                low_stock_drugs = [drug for drug in drugs if drug[3] < 50]
                
                if low_stock_drugs:
                    # Create a DataFrame for better display
                    low_stock_df = pd.DataFrame(low_stock_drugs, 
                                             columns=['Drug Name', 'Expiry Date', 'Usage', 'Quantity', 'Drug ID', 'Price'])
                    
                    # Add a "Restock" button for each drug
                    for idx, drug in low_stock_df.iterrows():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"**{drug['Drug Name']}**")
                            st.write(f"Current Stock: {drug['Quantity']}")
                        with col2:
                            # Create a form for each drug's restock
                            with st.form(key=f"restock_form_{drug['Drug ID']}"):
                                new_quantity = st.number_input(
                                    "Add Quantity",
                                    min_value=1,
                                    max_value=1000,
                                    value=50,
                                    key=f"quantity_{drug['Drug ID']}"
                                )
                                submitted = st.form_submit_button("Quick Restock")
                                if submitted:
                                    try:
                                        # Calculate total new quantity
                                        total_quantity = drug['Quantity'] + new_quantity
                                        # Update the drug quantity
                                        if update_drug_quantity(drug['Drug ID'], total_quantity):
                                            st.success(f"Successfully restocked {drug['Drug Name']} with {new_quantity} units!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to update quantity. Please try again.")
                                    except Exception as e:
                                        st.error(f"Error updating quantity: {str(e)}")
                        with col3:
                            st.write(f"₹{drug['Price']:.2f}")
                        st.markdown("---")
                else:
                    st.success("🎉 All drugs are well stocked! No low stock items.")
            else:
                st.info("No drugs found")

    elif admin_choice == "Customers":
        st.header("Customer Management")
        customers = customer_view_all_data()
        if customers:
            # Display customer statistics at the top
            st.subheader("Customer Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Customers", len(customers))
            
            with col2:
                insured_customers = sum(1 for c in customers if c[6] is not None)
                st.metric("Insured Customers", insured_customers)
            
            with col3:
                customers_with_ssn = sum(1 for c in customers if c[5] is not None)
                st.metric("Customers with SSN", customers_with_ssn)
            
            st.divider()  # Add a visual separator
            
            # Create a list to store customer data for display
            customer_data = []
            for customer in customers:
                # Get insurance company name if available
                insurance_name = "None"
                if customer[6]:  # If customer has insurance ID
                    try:
                        cursor = db_manager.get_cursor()
                        if cursor:
                            cursor.execute('SELECT CompName FROM Insurance WHERE InsuranceID = %s', (customer[6],))
                            result = cursor.fetchone()
                            if result:
                                insurance_name = result[0]
                    except mysql.connector.Error as err:
                        st.error(f"Error retrieving insurance information: {err}")
                
                # Mask sensitive information
                masked_customer = {
                    "Name": customer[0],
                    "Email": customer[2],
                    "State": customer[3],
                    "Phone": customer[4],
                    "SSN": customer[5] if customer[5] else "Not Set",
                    "Insurance": insurance_name
                }
                customer_data.append(masked_customer)

            # Display customer data in a table
            st.subheader("Customer Details")
            st.dataframe(pd.DataFrame(customer_data))
        else:
            st.info("No customers found")

    elif admin_choice == "Orders":
        st.header("Order Management")
        try:
            cursor = db_manager.get_cursor()
            if cursor:
                # Get available delivery agents count
                cursor.execute('''
                    SELECT COUNT(*) as available_agents
                    FROM DeliveryAgents
                    WHERE DA_Status = 'Available'
                ''')
                available_agents = cursor.fetchone()[0]
                
                # Display available agents count
                st.info(f"🚚 Available Delivery Agents: {available_agents}")
                
                if available_agents == 0:
                    st.warning("⚠️ No delivery agents are currently available. Please wait for agents to become available before assigning orders.")
            
                # Add filters at the top
                col1, col2 = st.columns(2)
                with col1:
                    # Status filter
                    status_filter = st.selectbox(
                        "Filter Orders by Status",
                        ["All", "Placed", "Confirmed", "Shipped", "Delivered", "Cancelled"],
                        key="admin_order_status_filter"
                    )
                
                with col2:
                    # Date filter
                    date_filter = st.date_input(
                        "Filter Orders by Date",
                        value=None,
                        key="admin_order_date_filter"
                    )
                
                # Get all orders grouped by base order ID
                orders = order_view_all_data()
                
                if orders:
                    # Group orders by their base ID (removing the drug-specific suffix)
                    grouped_orders = {}
                    for order in orders:
                        if len(order) < 4:  # Skip incomplete orders
                            continue
                        
                        # Extract base order ID (removing the drug ID suffix)
                        order_id_parts = order[3].split('_')
                        base_order_id = '_'.join(order_id_parts[:-1]) if len(order_id_parts) > 2 else order[3]
                        
                        # Get the status of the order
                        status = order[4] if len(order) > 4 else "Placed"
                        
                        # Get order date
                        order_date = order[8] if len(order) > 8 else None
                        
                        # Skip if filtered by status and doesn't match
                        if status_filter != "All" and status != status_filter:
                            continue
                        
                        # Skip if filtered by date and doesn't match
                        if date_filter and order_date:
                            order_date = order_date.date() if isinstance(order_date, datetime) else datetime.strptime(str(order_date), "%Y-%m-%d").date()
                            if order_date != date_filter:
                                continue
                        
                        if base_order_id not in grouped_orders:
                            grouped_orders[base_order_id] = {
                                'customer': order[0],
                                'items': [],
                                'status': status,
                                'address': order[5] if len(order) > 5 else "",
                                'payment': order[6] if len(order) > 6 else "",
                                'contact': order[7] if len(order) > 7 else "",
                                'date': order[8] if len(order) > 8 else "Unknown",
                                'status_update_time': order[9] if len(order) > 9 else "Unknown",
                                'total': 0
                            }
                        
                        # Get drug price for this item
                        price = 0
                        try:
                            cursor.execute('SELECT D_id FROM Drugs WHERE D_Name = %s', (order[1],))
                            drug_id = cursor.fetchone()
                            if drug_id:
                                price = get_drug_price(drug_id[0])
                        except:
                            pass
                        
                        # Add item to the order group
                        grouped_orders[base_order_id]['items'].append({
                            'name': order[1],
                            'quantity': order[2],
                            'price': price,
                            'subtotal': price * order[2]
                        })
                        grouped_orders[base_order_id]['total'] += price * order[2]
                    
                    # Display each order in an expandable section
                    for order_id, order_data in sorted(grouped_orders.items(), key=lambda x: x[1]['date'], reverse=True):
                        with st.expander(f"Order #{order_id} - {order_data['customer']} - {order_data['date']}"):
                            # Order summary
                            st.write(f"**Customer:** {order_data['customer']}")
                            st.write(f"**Status:** {order_data['status']}")
                            st.write(f"**Date:** {order_data['date']}")
                            # Format status update time
                            status_update_time = order_data['status_update_time']
                            if isinstance(status_update_time, datetime):
                                formatted_status_time = status_update_time.strftime("%Y-%m-%d %H:%M")
                            else:
                                formatted_status_time = str(status_update_time)
                            st.write(f"**Last Status Update:** {formatted_status_time}")
                            
                            # Items list
                            st.write("**Items:**")
                            for item in order_data['items']:
                                st.write(f"- {item['name']} (Qty: {item['quantity']}) - ₹{item['price']:.2f} × {item['quantity']} = ₹{item['subtotal']:.2f}")
                            
                            st.write(f"**Total Amount:** ₹{order_data['total']:.2f}")
                            st.write(f"**Delivery Address:** {order_data['address']}")
                            st.write(f"**Contact Number:** {order_data['contact']}")
                            st.write(f"**Payment Method:** {order_data['payment']}")
                            
                            # Add status update buttons
                            if order_data['status'] != "Delivered" and order_data['status'] != "Cancelled":
                                st.subheader("Update Order Status")
                                
                                # Define available status transitions
                                status_transitions = {
                                    "Placed": ["Confirmed", "Cancelled"],
                                    "Confirmed": ["Shipped", "Cancelled"],
                                    "Shipped": ["Delivered", "Cancelled"],
                                    "Delivered": [],  # No further transitions allowed
                                    "Cancelled": []   # No further transitions allowed
                                }
                                
                                # Get available status options based on current status
                                available_statuses = status_transitions.get(order_data['status'], [])
                                
                                if available_statuses:
                                    new_status = st.selectbox(
                                        "Select new status",
                                        available_statuses,
                                        key=f"status_{order_id}"
                                    )
                                    
                                    if st.button("Update Status", key=f"update_{order_id}"):
                                        try:
                                            if update_order_status(order_id, new_status):
                                                st.success(f"Order status updated to {new_status}")
                                                if new_status == "Confirmed":
                                                    st.info("Order is now available to active delivery agents")
                                                st.rerun()
                                            else:
                                                st.error("Failed to update order status. Please try again.")
                                        except Exception as e:
                                            st.error(f"Error updating status: {str(e)}")
                                else:
                                    st.info("No further status updates available for this order")
                else:
                    st.info("No orders found")
        except mysql.connector.Error as err:
            st.error(f"Error retrieving orders: {err}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

    elif admin_choice == "Prescriptions":
        st.header("Prescription Management")
        prescriptions = view_prescriptions()
        if prescriptions:
            st.write(pd.DataFrame(prescriptions, 
                                columns=["ID", "Patient SSN", "Doctor ID", "Date", "Medications"]))
        else:
            st.info("No prescriptions found")

    elif admin_choice == "Insurance":
        st.header("Insurance Management")

        with st.expander("Add Insurance", expanded=True):
            with st.form("add_insurance_form"):
                comp_name = st.text_input("Company Name")
                coverage = st.number_input("Coverage Percentage", min_value=0.0, max_value=100.0, step=0.1)

                submitted = st.form_submit_button("Add Insurance")
                if submitted:
                    if comp_name and coverage > 0:
                        try:
                            cursor = db_manager.get_cursor()
                            if cursor:
                                cursor.execute('INSERT INTO Insurance (CompName, Coverage) VALUES (%s, %s)', 
                                             (comp_name, coverage))
                                db_manager.commit()
                                st.success("Insurance added successfully")
                        except mysql.connector.Error as err:
                            st.error(f"Error adding insurance: {err}")
                    else:
                        st.warning("Please fill all fields")

        st.subheader("Existing Insurance Providers")
        try:
            cursor = db_manager.get_cursor()
            if cursor:
                cursor.execute('SELECT * FROM Insurance')
                insurances = cursor.fetchall()
                if insurances:
                    st.write(pd.DataFrame(insurances, columns=["ID", "Company Name", "Coverage %"]))
                else:
                    st.info("No insurance providers found")
        except mysql.connector.Error as err:
            st.error(f"Error retrieving insurance data: {err}")

    elif admin_choice == "Billing":
        st.header("Billing Management")
    
        # View billing history with detailed items
        st.subheader("Complete Billing History")
        
        try:
            cursor = db_manager.get_cursor()
            if cursor:
                # Get all bills
                cursor.execute('''
                    SELECT b.BillID, b.CustomerPhone, b.BillDate, b.TotalAmount 
                    FROM Billing b 
                    ORDER BY b.BillDate DESC
                ''')
                bills = cursor.fetchall()
                
                if bills:
                    # Group bills by date
                    bills_by_date = {}
                    for bill in bills:
                        bill_date = bill[2].date() if isinstance(bill[2], datetime) else datetime.strptime(str(bill[2]), "%Y-%m-%d").date()
                        if bill_date not in bills_by_date:
                            bills_by_date[bill_date] = []
                        bills_by_date[bill_date].append(bill)
                    
                    # Display bills grouped by date
                    for date in sorted(bills_by_date.keys(), reverse=True):
                        # Calculate total for this date
                        total_amount = sum(bill[3] for bill in bills_by_date[date])
                        
                        # Show date and total amount at the top
                        st.subheader(f"Bills for {date}")
                        st.markdown(f"**Total Amount: ₹{total_amount:.2f}**")
                        
                        # Display individual bills
                        for bill in bills_by_date[date]:
                            with st.expander(f"Bill #{bill[0]} - {bill[1]}"):
                                st.write(f"**Customer:** {bill[1]}")
                                st.write(f"**Date:** {bill[2]}")
                                st.write(f"**Amount:** ₹{bill[3]:.2f}")
                        
                        st.markdown("---")  # Add a separator between dates
                else:
                    st.info("No billing records found")
        except mysql.connector.Error as err:
            st.error(f"Error retrieving billing data: {err}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

    elif admin_choice == "Pharmacy Performance":
        st.title("📊 Pharmacy Performance Dashboard")
        
        # Create a container for the entire dashboard
        dashboard_container = st.container()
        
        with dashboard_container:
            try:
                cursor = db_manager.get_cursor()
                if cursor:
                    # 1. Key Performance Metrics
                    st.subheader("📈 Key Performance Metrics")
                    
                    # Get current date and time
                    current_date = datetime.now().date()
                    current_month = current_date.month
                    current_year = current_date.year
                    
                    # Get total customers
                    cursor.execute('SELECT COUNT(*) FROM Customers')
                    total_customers = cursor.fetchone()[0]
                    cursor.fetchall()  # Clear any remaining results
                    
                    # Get today's active customers
                    cursor.execute('''
                        SELECT COUNT(DISTINCT O_Name) 
                        FROM Orders 
                        WHERE DATE(OrderDate) = CURDATE()
                    ''')
                    today_active = cursor.fetchone()[0]
                    cursor.fetchall()  # Clear any remaining results
                    
                    # Get monthly active customers
                    cursor.execute('''
                        SELECT COUNT(DISTINCT O_Name) 
                        FROM Orders 
                        WHERE MONTH(OrderDate) = MONTH(CURDATE()) 
                        AND YEAR(OrderDate) = YEAR(CURDATE())
                    ''')
                    monthly_active = cursor.fetchone()[0]
                    cursor.fetchall()  # Clear any remaining results
                    
                    # Get revenue metrics
                    cursor.execute('SELECT SUM(TotalAmount) FROM Billing')
                    total_revenue = cursor.fetchone()[0] or 0
                    cursor.fetchall()  # Clear any remaining results
                    
                    cursor.execute('''
                        SELECT SUM(TotalAmount) 
                        FROM Billing 
                        WHERE DATE(BillDate) = CURDATE()
                    ''')
                    today_revenue = cursor.fetchone()[0] or 0
                    cursor.fetchall()  # Clear any remaining results
                    
                    cursor.execute('''
                        SELECT SUM(TotalAmount) 
                        FROM Billing 
                        WHERE MONTH(BillDate) = MONTH(CURDATE()) 
                        AND YEAR(BillDate) = YEAR(CURDATE())
                    ''')
                    monthly_revenue = cursor.fetchone()[0] or 0
                    cursor.fetchall()  # Clear any remaining results
                    
                    # Display metrics in a grid
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("👥 Total Customers", total_customers)
                        st.metric("📊 Today's Active", today_active)
                        st.metric("📈 Monthly Active", monthly_active)
                    
                    with col2:
                        st.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
                        st.metric("💵 Today's Revenue", f"₹{today_revenue:,.2f}")
                        st.metric("📊 Monthly Revenue", f"₹{monthly_revenue:,.2f}")
                    
                    with col3:
                        # Calculate and display average order value
                        cursor.execute('SELECT COUNT(*) FROM Orders')
                        total_orders = cursor.fetchone()[0] or 1
                        cursor.fetchall()  # Clear any remaining results
                        avg_order_value = total_revenue / total_orders
                        st.metric("💎 Average Order Value", f"₹{avg_order_value:,.2f}")
                        
                        # Calculate conversion rate
                        if total_customers > 0:
                            conversion_rate = (monthly_active / total_customers) * 100
                            st.metric("🔄 Monthly Conversion", f"{conversion_rate:.1f}%")
                        
                        # Calculate repeat customer rate
                        cursor.execute('''
                            SELECT COUNT(DISTINCT O_Name) 
                            FROM Orders 
                            GROUP BY O_Name 
                            HAVING COUNT(*) > 1
                        ''')
                        repeat_customers = cursor.fetchone()[0] or 0
                        cursor.fetchall()  # Clear any remaining results
                        if total_customers > 0:
                            repeat_rate = (repeat_customers / total_customers) * 100
                            st.metric("🔄 Repeat Rate", f"{repeat_rate:.1f}%")
                    
                    st.markdown("---")
                    
                    # 2. Monthly Revenue & Orders Trend
                    st.subheader("📊 Monthly Trends")
                    
                    # Get last 6 months data
                    cursor.execute('''
                        SELECT 
                            DATE_FORMAT(BillDate, '%Y-%m') as month,
                            COUNT(DISTINCT b.BillID) as order_count,
                            SUM(b.TotalAmount) as revenue
                        FROM Billing b
                        WHERE BillDate >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                        GROUP BY DATE_FORMAT(BillDate, '%Y-%m')
                        ORDER BY month
                    ''')
                    monthly_data = cursor.fetchall()
                    
                    if monthly_data:
                        # Create DataFrame for the chart
                        df_monthly = pd.DataFrame(monthly_data, columns=['Month', 'Orders', 'Revenue'])
                        
                        # Create two columns for the charts
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.line_chart(df_monthly.set_index('Month')['Revenue'], 
                                        use_container_width=True)
                            st.caption("Monthly Revenue Trend")
                        
                        with col2:
                            st.line_chart(df_monthly.set_index('Month')['Orders'], 
                                        use_container_width=True)
                            st.caption("Monthly Orders Trend")
                    
                    st.markdown("---")
                    
                    # 3. Top Performing Drugs
                    st.subheader("💊 Top Performing Drugs")
                    
                    cursor.execute('''
                        SELECT 
                            d.D_Name,
                            COUNT(DISTINCT o.O_id) as order_count,
                            SUM(o.O_Qty) as total_quantity,
                            COALESCE(SUM(o.O_Qty * dp.PricePerUnit), 0) as total_revenue
                        FROM Drugs d
                        JOIN Orders o ON d.D_Name = o.O_Items
                        JOIN Drug_Pricing dp ON d.D_id = dp.DrugID
                        WHERE o.Status = 'Delivered'
                        GROUP BY d.D_Name
                        ORDER BY total_revenue DESC
                        LIMIT 5
                    ''')
                    top_drugs = cursor.fetchall()
                    
                    if top_drugs:
                        df_top_drugs = pd.DataFrame(top_drugs, 
                                                  columns=['Drug Name', 'Orders', 'Quantity Sold', 'Revenue'])
                        df_top_drugs['Revenue'] = df_top_drugs['Revenue'].apply(lambda x: f"₹{float(x):,.2f}")
                        st.dataframe(df_top_drugs, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # 4. Inventory Alerts
                    st.subheader("⚠️ Inventory Alerts")
                    
                    cursor.execute('''
                        SELECT 
                            D_Name,
                            D_Qty,
                            D_ExpDate,
                            CASE 
                                WHEN D_Qty < 50 THEN 'Low Stock'
                                WHEN D_ExpDate <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'Expiring Soon'
                                ELSE 'Normal'
                            END as alert_type
                        FROM Drugs
                        WHERE D_Qty < 50 OR D_ExpDate <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                        ORDER BY 
                            CASE 
                                WHEN D_Qty < 50 THEN 1
                                WHEN D_ExpDate <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 2
                                ELSE 3
                            END,
                            D_Qty ASC,
                            D_ExpDate ASC
                    ''')
                    inventory_alerts = cursor.fetchall()
                    
                    if inventory_alerts:
                        df_alerts = pd.DataFrame(inventory_alerts, 
                                               columns=['Drug Name', 'Current Stock', 'Expiry Date', 'Alert Type'])
                        st.dataframe(df_alerts, use_container_width=True)
                    else:
                        st.success("✅ No inventory alerts at this time")
                    
                    # Add refresh button at the bottom
                    st.markdown("---")
                    if st.button("🔄 Refresh Dashboard"):
                        st.rerun()
                        
            except mysql.connector.Error as err:
                st.error(f"Error retrieving performance data: {err}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
            finally:
                if cursor:
                    cursor.close()

    elif admin_choice == "Delivery Agents":
        st.title("🚚 Delivery Agent Management")
        
        try:
            cursor = db_manager.get_cursor()
            if cursor:
                # Overall Delivery Agent Metrics
                st.subheader("📊 Overall Delivery Agent Metrics")
                
                # Get overall statistics
                cursor.execute('''
                    SELECT 
                        COUNT(DISTINCT da.DA_Phone) as total_agents,
                        COUNT(DISTINCT CASE WHEN o.Status = 'Delivered' THEN o.O_id END) as successful_deliveries,
                        AVG(TIMESTAMPDIFF(MINUTE, o.OrderDate, o.StatusUpdateTime)) as avg_delivery_time,
                        COUNT(DISTINCT CASE WHEN o.Status IN ('Placed', 'Confirmed', 'Shipped') THEN o.O_id END) as active_deliveries,
                        COALESCE(SUM(
                            CASE 
                                WHEN o.Status = 'Delivered' 
                                THEN o.O_Qty * (
                                    SELECT PricePerUnit 
                                    FROM Drug_Pricing dp 
                                    JOIN Drugs d ON dp.DrugID = d.D_id 
                                    WHERE d.D_Name = o.O_Items
                                )
                                ELSE 0 
                            END
                        ), 0) as total_revenue
                    FROM DeliveryAgents da
                    LEFT JOIN Orders o ON da.DA_Phone = o.DeliveryAgentPhone
                ''')
                overall_stats = cursor.fetchone()
                
                # Display metrics in cards
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("👥 Total Agents", int(overall_stats[0] or 0))
                with col2:
                    st.metric("✅ Successful Deliveries", int(overall_stats[1] or 0))
                with col3:
                    avg_time = int(overall_stats[2] or 0)
                    st.metric("⏱️ Avg Delivery Time", f"{avg_time} mins")
                with col4:
                    st.metric("📦 Active Deliveries", int(overall_stats[3] or 0))
                with col5:
                    revenue = float(overall_stats[4] or 0)
                    st.metric("💰 Total Revenue", f"₹{revenue:,.2f}")

                # Live Delivery Agent Status Board
                st.subheader("📦 Live Delivery Agent Status")
                
                # Get agent statuses
                cursor.execute('''
                    SELECT 
                        da.DA_Name,
                        da.DA_Phone,
                        da.DA_BikeNumber,
                        da.DA_Status,
                        o.O_id as current_order
                    FROM DeliveryAgents da
                    LEFT JOIN Orders o ON da.DA_Phone = o.DeliveryAgentPhone 
                        AND o.Status IN ('Placed', 'Confirmed', 'Shipped')
                ''')
                agent_statuses = cursor.fetchall()
                
                # Create three columns for different statuses
                col1, col2, col3 = st.columns(3)
                
                # Available Agents
                with col1:
                    st.markdown("### 🟢 Available")
                    available_agents = [a for a in agent_statuses if a[3] == 'Available']
                    if available_agents:
                        for agent in available_agents:
                            with st.expander(f"🚚 {agent[0]}"):
                                st.write(f"**Phone:** {agent[1]}")
                                st.write(f"**Bike:** {agent[2]}")
                                if agent[4]:
                                    st.write(f"**Current Order:** {agent[4]}")
                    else:
                        st.info("No available agents")
                
                # Busy Agents
                with col2:
                    st.markdown("### 🟠 Busy")
                    busy_agents = [a for a in agent_statuses if a[3] == 'Busy']
                    if busy_agents:
                        for agent in busy_agents:
                            with st.expander(f"🚚 {agent[0]}"):
                                st.write(f"**Phone:** {agent[1]}")
                                st.write(f"**Bike:** {agent[2]}")
                                if agent[4]:
                                    st.write(f"**Current Order:** {agent[4]}")
                    else:
                        st.info("No busy agents")
                
                # Offline Agents
                with col3:
                    st.markdown("### 🔴 Offline")
                    offline_agents = [a for a in agent_statuses if a[3] == 'Offline']
                    if offline_agents:
                        for agent in offline_agents:
                            with st.expander(f"🚚 {agent[0]}"):
                                st.write(f"**Phone:** {agent[1]}")
                                st.write(f"**Bike:** {agent[2]}")
                                if agent[4]:
                                    st.write(f"**Current Order:** {agent[4]}")
                    else:
                        st.info("No offline agents")

                # Individual Agent Performance Table
                st.subheader("👤 Individual Agent Performance")
                
                cursor.execute('''
                    SELECT 
                        da.DA_Name,
                        da.DA_Phone,
                        da.DA_BikeNumber,
                        da.DA_Status,
                        COUNT(DISTINCT o.O_id) as total_deliveries,
                        COUNT(DISTINCT CASE WHEN o.Status = 'Delivered' THEN o.O_id END) as successful_deliveries,
                        COUNT(DISTINCT CASE WHEN o.Status = 'Cancelled' THEN o.O_id END) as cancelled_deliveries,
                        AVG(TIMESTAMPDIFF(MINUTE, o.OrderDate, o.StatusUpdateTime)) as avg_delivery_time
                    FROM DeliveryAgents da
                    LEFT JOIN Orders o ON da.DA_Phone = o.DeliveryAgentPhone
                    GROUP BY da.DA_Phone, da.DA_Name, da.DA_BikeNumber, da.DA_Status
                    ORDER BY total_deliveries DESC
                ''')
                agent_performance = cursor.fetchall()
                
                if agent_performance:
                    # Create DataFrame for better display
                    df = pd.DataFrame(agent_performance, columns=[
                        "Agent Name", "Phone", "Bike No", "Status", 
                        "Total Deliveries", "Delivered", "Cancelled", 
                        "Avg Time (mins)"
                    ])
                    
                    # Add status icons
                    status_icons = {
                        'Available': '🟢',
                        'Busy': '🟠',
                        'Offline': '🔴'
                    }
                    df['Status'] = df['Status'].map(lambda x: f"{status_icons.get(x, '⚪')} {x}")
                    
                    # Format average time
                    df['Avg Time (mins)'] = df['Avg Time (mins)'].apply(lambda x: f"{int(x or 0)} mins")
                    
                    # Display the table
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No agent performance data available")

                # Add auto-refresh
                st.markdown("---")
                st.markdown("🔄 Auto-refreshing every 30 seconds")
                time.sleep(30)
                st.rerun()

        except mysql.connector.Error as err:
            st.error(f"Error accessing database: {err}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

# Add this after the create_tables function
def create_delivery_agent_table():
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return

        cursor.execute('''CREATE TABLE IF NOT EXISTS DeliveryAgents(
            DA_Name VARCHAR(50) NOT NULL,
            DA_Phone VARCHAR(15) PRIMARY KEY NOT NULL,
            DA_Password VARCHAR(100) NOT NULL,
            DA_Address TEXT NOT NULL,
            DA_BikeNumber VARCHAR(20),
            DA_Status VARCHAR(20) DEFAULT 'Available'
        )''')
        db_manager.commit()
    except mysql.connector.Error as err:
        st.error(f"Error creating delivery agent table: {err}")

# Add delivery agent functions
def delivery_agent_add_data(name, phone, password, address):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False

        # Check if phone exists
        cursor.execute("SELECT DA_Phone FROM DeliveryAgents WHERE DA_Phone = %s", (phone,))
        if cursor.fetchone():
            st.error("Phone number already registered")
            return False

        # Hash password
        hashed_pass = hash_password(password)

        # Insert delivery agent without bike number
        cursor.execute('''INSERT INTO DeliveryAgents(DA_Name, DA_Phone, DA_Password, DA_Address) 
            VALUES (%s, %s, %s, %s)''', (name, phone, hashed_pass, address))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error adding delivery agent: {err}")
        return False

def update_delivery_agent_profile(phone, bike_number=None, address=None):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False

        update_fields = []
        update_values = []
        
        if bike_number is not None:
            update_fields.append("DA_BikeNumber = %s")
            update_values.append(bike_number)
            
        if address is not None:
            update_fields.append("DA_Address = %s")
            update_values.append(address)
            
        if not update_fields:
            return False
            
        update_values.append(phone)
        query = f"UPDATE DeliveryAgents SET {', '.join(update_fields)} WHERE DA_Phone = %s"
        
        cursor.execute(query, tuple(update_values))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error updating profile: {err}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False

def delivery_agent_authenticate(phone, password):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
        cursor.execute('SELECT DA_Password FROM DeliveryAgents WHERE DA_Phone = %s', (phone,))
        agent_password = cursor.fetchone()
        if agent_password:
            hashed_input_pass = hash_password(password)
            return agent_password[0] == hashed_input_pass
        return False
    except mysql.connector.Error as err:
        st.error(f"Authentication error: {err}")
        return False

def get_delivery_agent_orders(phone):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return []
        cursor.execute('''
            SELECT O_Name, O_Items, O_Qty, O_id, Status, 
                   DeliveryAddress, PaymentMethod, ContactNumber, OrderDate,
                   DeliveryAgentName, DeliveryAgentPhone, DeliveryAgentBike
            FROM Orders
            WHERE Status = 'Confirmed'
            ORDER BY OrderDate DESC
        ''')
        return cursor.fetchall() or []
    except mysql.connector.Error as err:
        st.error(f"Error retrieving orders: {err}")
        return []

def update_delivery_agent_status(phone, status):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            return False
        cursor.execute('UPDATE DeliveryAgents SET DA_Status = %s WHERE DA_Phone = %s', (status, phone))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error updating status: {err}")
        return False

# Add delivery agent dashboard
def delivery_agent_dashboard(phone):
    st.title("Delivery Agent Dashboard")
    
    try:
        # Show current status
        cursor = db_manager.get_cursor()
        if not cursor:
            st.error("Database connection error. Please try again later.")
            return
            
        # Get delivery agent information
        cursor.execute('''
            SELECT DA_Name, DA_Status, DA_BikeNumber, DA_Address 
            FROM DeliveryAgents 
            WHERE DA_Phone = %s
        ''', (phone,))
        agent = cursor.fetchone()
        if not agent:
            st.error("Agent information not found. Please contact support.")
            return
            
        # Get delivery statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_deliveries,
                COUNT(CASE WHEN Status = 'Delivered' THEN 1 END) as completed_deliveries,
                COUNT(CASE WHEN Status = 'Shipped' THEN 1 END) as in_progress_deliveries
            FROM Orders 
            WHERE DeliveryAgentPhone = %s
        ''', (phone,))
        stats = cursor.fetchone()
        
        # Profile Section
        st.subheader("Profile Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {agent[0]}")
            st.write(f"**Phone:** {phone}")
            st.write(f"**Status:** {agent[1]}")
            st.write(f"**Bike Number:** {agent[2] if agent[2] else 'Not Set'}")
            st.write(f"**Address:** {agent[3]}")
        
        with col2:
            st.write("**Delivery Statistics**")
            st.write(f"**Total Orders Handled:** {stats[0]}")
            st.write(f"**Completed Deliveries:** {stats[1]}")
            st.write(f"**In Progress:** {stats[2]}")
            if stats[0] > 0:
                completion_rate = (stats[1] / stats[0]) * 100
                st.write(f"**Completion Rate:** {completion_rate:.1f}%")
        
        # Profile Update Section
        with st.expander("Update Profile", expanded=False):
            bike_number = st.text_input("Bike Number", value=agent[2] if agent[2] else "", 
                                      placeholder="Enter your bike number")
            address = st.text_input("Address", value=agent[3] if agent[3] else "",
                                  placeholder="Enter your address")
            
            if st.button("Update Profile"):
                if update_delivery_agent_profile(phone, bike_number, address):
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update profile. Please try again.")
        
        # Password Change Section
        with st.expander("Change Password", expanded=False):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.button("Change Password"):
                if not current_password or not new_password or not confirm_password:
                    st.error("All fields are required")
                elif new_password != confirm_password:
                    st.error("New passwords do not match")
                else:
                    # Verify current password
                    cursor.execute('SELECT DA_Password FROM DeliveryAgents WHERE DA_Phone = %s', (phone,))
                    stored_password = cursor.fetchone()
                    if stored_password and stored_password[0] == hash_password(current_password):
                        # Update password
                        cursor.execute('UPDATE DeliveryAgents SET DA_Password = %s WHERE DA_Phone = %s',
                                     (hash_password(new_password), phone))
                        db_manager.commit()
                        st.success("Password changed successfully!")
                    else:
                        st.error("Current password is incorrect")
        
        st.markdown("---")
        
        # Status update
        new_status = st.selectbox(
            "Update your status",
            ["Available", "Busy", "Offline"],
            index=["Available", "Busy", "Offline"].index(agent[1])
        )
        
        if new_status != agent[1]:
            if update_delivery_agent_status(phone, new_status):
                st.success(f"Status updated to {new_status}")
                st.rerun()
            else:
                st.error("Failed to update status. Please try again.")

        # Show available orders
        st.subheader("Available Orders")
        orders = get_delivery_agent_orders(phone)
        
        if orders:
            grouped_orders = {}
            for order in orders:
                if len(order) < 4:
                    continue
                    
                order_id_parts = order[3].split('_')
                base_order_id = '_'.join(order_id_parts[:-1]) if len(order_id_parts) > 2 else order[3]
                
                if base_order_id not in grouped_orders:
                    grouped_orders[base_order_id] = {
                        'customer': order[0],
                        'items': [],
                        'status': order[4] if len(order) > 4 else "Placed",
                        'address': order[5] if len(order) > 5 else "",
                        'contact': order[7] if len(order) > 7 else "",
                        'date': order[8] if len(order) > 8 else "Unknown",
                        'status_update_time': order[9] if len(order) > 9 else "Unknown",
                        'delivery_agent': order[10] if len(order) > 10 else None,
                        'delivery_agent_phone': order[11] if len(order) > 11 else None,
                        'delivery_agent_bike': order[12] if len(order) > 12 else None,
                        'total': 0
                    }
                
                # Get drug price for this item
                price = 0
                try:
                    cursor.execute('SELECT D_id FROM Drugs WHERE D_Name = %s', (order[1],))
                    drug_id = cursor.fetchone()
                    if drug_id:
                        price = get_drug_price(drug_id[0])
                except:
                    pass
                
                # Add item to the order group with price information
                grouped_orders[base_order_id]['items'].append({
                    'name': order[1],
                    'quantity': order[2],
                    'price': price,
                    'subtotal': price * order[2]
                })
                grouped_orders[base_order_id]['total'] += price * order[2]
            
            # Show orders in two sections
            st.subheader("New Orders to Accept")
            new_orders = {k: v for k, v in grouped_orders.items() if v['status'] == 'Confirmed'}
            if new_orders:
                for order_id, order_data in sorted(new_orders.items(), key=lambda x: x[1]['date'], reverse=True):
                    with st.expander(f"Order #{order_id} - {order_data['customer']}"):
                        st.write(f"**Customer:** {order_data['customer']}")
                        st.write(f"**Status:** {order_data['status']}")
                        st.write(f"**Order Date:** {order_data['date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(order_data['date'], datetime) else order_data['date']}")
                        st.write(f"**Delivery Address:** {order_data['address']}")
                        st.write(f"**Contact Number:** {order_data['contact']}")
                        
                        # Display items with prices
                        st.write("**Items:**")
                        for item in order_data['items']:
                            st.write(f"- {item['name']} (Qty: {item['quantity']}) - ₹{item['price']:.2f} × {item['quantity']} = ₹{item['subtotal']:.2f}")
                        
                        # Display total amount
                        st.write(f"**Total Amount:** ₹{order_data['total']:.2f}")
                        
                        if st.button("Accept Order", key=f"accept_{order_id}"):
                            if update_order_status(order_id, "Shipped", phone):
                                st.success("Order accepted and marked as shipped!")
                                st.rerun()
                            else:
                                st.error("Failed to update order status. Please try again.")
            else:
                st.info("No new orders to accept")
            
            st.markdown("---")
            
            # Show orders in progress
            st.subheader("Orders in Progress")
            cursor.execute('''
                SELECT O_Name, O_Items, O_Qty, O_id, Status, 
                       DeliveryAddress, PaymentMethod, ContactNumber, OrderDate,
                       DeliveryAgentName, DeliveryAgentPhone, DeliveryAgentBike,
                       StatusUpdateTime
                FROM Orders
                WHERE Status = 'Shipped' AND DeliveryAgentPhone = %s
                ORDER BY OrderDate DESC
            ''', (phone,))
            in_progress_orders = cursor.fetchall()
            
            if in_progress_orders:
                for order in in_progress_orders:
                    with st.expander(f"Order #{order[3]} - {order[0]}"):
                        st.write(f"**Customer:** {order[0]}")
                        st.write(f"**Status:** {order[4]}")
                        st.write(f"**Order Date:** {order[8].strftime('%Y-%m-%d %H:%M:%S') if isinstance(order[8], datetime) else order[8]}")
                        st.write(f"**Accepted On:** {order[12].strftime('%Y-%m-%d %H:%M:%S') if isinstance(order[12], datetime) else 'N/A'}")
                        st.write(f"**Delivery Address:** {order[5]}")
                        st.write(f"**Contact Number:** {order[7]}")
                        
                        if st.button("Mark as Delivered", key=f"deliver_{order[3]}"):
                            if update_order_status(order[3], "Delivered", phone):
                                st.success("Order marked as delivered!")
                                st.rerun()
                            else:
                                st.error("Failed to update order status. Please try again.")
            else:
                st.info("No orders in progress")
        else:
            st.info("No confirmed orders available at the moment")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

def reset_customer_password(phone, new_password):
    try:
        cursor = db_manager.get_cursor()
        if not cursor:
            st.error("Database connection error. Please try again later.")
            return False
            
        # Check if phone exists
        cursor.execute('SELECT C_Number FROM Customers WHERE C_Number = %s', (phone,))
        if not cursor.fetchone():
            st.error("Phone number not found. Please check your phone number.")
            return False
            
        # Hash the new password
        hashed_password = hash_password(new_password)
        
        # Update the password
        cursor.execute('UPDATE Customers SET C_Password = %s WHERE C_Number = %s', 
                      (hashed_password, phone))
        db_manager.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.connection.rollback()
        return False

# Function to load Lottie animation from URL
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            st.error(f"Failed to load animation: HTTP {r.status_code}")
            return None
        return r.json()
    except Exception as e:
        st.error(f"Error loading animation: {str(e)}")
        return None

# Example Lottie animation (you can find more at lottiefiles.com)
lottie_animation = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_ktwnwv5m.json")

def show_loading_animation():
    """Show a loading animation while the system initializes"""
    with st.spinner('Initializing MedCare System...'):
        time.sleep(1)  # Simulate loading time
        st.success('System Ready!')

# Main App
def main():
    # Set page configuration
    st.set_page_config(
        page_title="Pharmacy Management System",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.admin_logged_in = False
        st.session_state.delivery_agent_logged_in = False
        st.session_state.delivery_agent_phone = None
        st.session_state.show_welcome = True
    if 'redirect' not in st.session_state:
        st.session_state.redirect = False

    try:
        # Create tables and initialize sample data
        create_tables()
        initialize_sample_data()

        # Show welcome screen if not logged in
        if not (st.session_state.logged_in or st.session_state.admin_logged_in or st.session_state.delivery_agent_logged_in):
            if st.session_state.show_welcome:
                st.markdown("""
                    <style>
                    .main {
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                        color: white;
                    }
                    .big-title {
                        font-size: 4rem;
                        font-weight: bold;
                        text-align: center;
                        margin-top: 2rem;
                        background: linear-gradient(45deg, #00ffcc, #00b4d8);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        text-shadow: 0 0 30px rgba(0, 255, 204, 0.3);
                        animation: glow 2s ease-in-out infinite alternate;
                    }
                    @keyframes glow {
                        from {
                            text-shadow: 0 0 20px rgba(0, 255, 204, 0.3),
                                       0 0 40px rgba(0, 255, 204, 0.2),
                                       0 0 60px rgba(0, 255, 204, 0.1);
                        }
                        to {
                            text-shadow: 0 0 30px rgba(0, 255, 204, 0.5),
                                       0 0 60px rgba(0, 255, 204, 0.3),
                                       0 0 90px rgba(0, 255, 204, 0.2);
                        }
                    }
                    .subtitle {
                        font-size: 1.5rem;
                        text-align: center;
                        margin-bottom: 2rem;
                        color: #e0e0e0;
                        text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
                    }
                    .subtitle-container {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 1rem;
                        margin: 2rem 0;
                    }
                    .subtitle-line {
                        font-size: 1.8rem;
                        background: linear-gradient(45deg, #00ffcc, #00b4d8, #0077b6);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        text-align: center;
                        opacity: 0;
                        transform: translateY(20px);
                        animation: fadeInUp 0.8s ease forwards;
                    }
                    .subtitle-line:nth-child(2) {
                        animation-delay: 0.3s;
                    }
                    .subtitle-line:nth-child(3) {
                        animation-delay: 0.6s;
                    }
                    @keyframes fadeInUp {
                        from {
                            opacity: 0;
                            transform: translateY(20px);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0);
                        }
                    }
                    .subtitle-highlight {
                        color: #00ffcc;
                        font-weight: bold;
                        text-shadow: 0 0 15px rgba(0, 255, 204, 0.5);
                    }
                    .subtitle-decoration {
                        width: 150px;
                        height: 3px;
                        background: linear-gradient(90deg, transparent, #00ffcc, transparent);
                        margin: 1rem auto;
                        position: relative;
                        overflow: hidden;
                    }
                    .subtitle-decoration::after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, #fff, transparent);
                        animation: shine 2s infinite;
                    }
                    @keyframes shine {
                        to {
                            left: 100%;
                        }
                    }
                    .feature-row-vfx {
                        display: flex;
                        justify-content: center;
                        gap: 2.5rem;
                        flex-wrap: wrap;
                        margin-top: 3rem;
                    }
                    .feature-card-vfx {
                        background: rgba(26, 26, 46, 0.8);
                        border-radius: 20px;
                        box-shadow: 0 0 30px 10px rgba(0, 255, 204, 0.1),
                                   0 0 10px 2px rgba(0, 191, 174, 0.1);
                        padding: 2rem 1.5rem;
                        min-width: 280px;
                        max-width: 340px;
                        transition: all 0.4s ease;
                        border: 2px solid rgba(0, 255, 204, 0.1);
                        position: relative;
                        overflow: hidden;
                        backdrop-filter: blur(10px);
                    }
                    .feature-card-vfx::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(
                            90deg,
                            transparent,
                            rgba(0, 255, 204, 0.2),
                            transparent
                        );
                        transition: 0.5s;
                    }
                    .feature-card-vfx:hover::before {
                        left: 100%;
                    }
                    .feature-card-vfx:hover {
                        transform: translateY(-10px) scale(1.02);
                        box-shadow: 0 0 60px 20px rgba(0, 255, 204, 0.2),
                                   0 0 20px 4px rgba(0, 191, 174, 0.2);
                        border-color: rgba(0, 255, 204, 0.3);
                    }
                    .feature-icon-vfx {
                        font-size: 3rem;
                        margin-bottom: 1.5rem;
                        background: linear-gradient(45deg, #00ffcc, #00b4d8);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        text-align: center;
                        filter: drop-shadow(0 0 10px rgba(0, 255, 204, 0.3));
                    }
                    .feature-title-vfx {
                        font-size: 1.5rem;
                        color: #fff;
                        font-weight: bold;
                        margin-bottom: 1rem;
                        text-align: center;
                        text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
                    }
                    .feature-desc-vfx {
                        color: #b0e0e6;
                        font-size: 1.1rem;
                        font-weight: 500;
                        text-align: center;
                        line-height: 1.6;
                    }
                    .why-row {
                        display: flex;
                        gap: 2.5rem;
                        justify-content: center;
                        flex-wrap: wrap;
                        margin-top: 2rem;
                    }
                    .why-col {
                        display: flex;
                        flex-direction: column;
                        gap: 1.5rem;
                    }
                    .why-item {
                        background: rgba(26, 26, 46, 0.8);
                        border-radius: 16px;
                        padding: 1.5rem;
                        box-shadow: 0 0 20px 5px rgba(0, 255, 204, 0.1);
                        color: #fff;
                        font-size: 1.2rem;
                        border: 2px solid rgba(0, 255, 204, 0.1);
                        transition: all 0.3s ease;
                        backdrop-filter: blur(10px);
                    }
                    .why-item:hover {
                        transform: translateX(10px);
                        box-shadow: 0 0 30px 10px rgba(0, 255, 204, 0.2);
                        border-color: rgba(0, 255, 204, 0.3);
                    }
                    .why-icon {
                        color: #00ffcc;
                        font-size: 1.4rem;
                        margin-right: 0.8rem;
                        vertical-align: middle;
                        filter: drop-shadow(0 0 5px rgba(0, 255, 204, 0.5));
                    }
                    .why-desc {
                        color: #b0e0e6;
                        font-size: 1.1rem;
                        margin-top: 0.5rem;
                        line-height: 1.6;
                    }
                    .stButton > button {
                        background: linear-gradient(45deg, #00ffcc, #00b4d8);
                        color: #1a1a2e;
                        padding: 1.5rem 4rem;
                        border-radius: 50px;
                        border: none;
                        font-size: 1.8rem;
                        font-weight: bold;
                        box-shadow: 0 0 40px 10px rgba(0, 255, 204, 0.2);
                        transition: all 0.4s ease;
                        cursor: pointer;
                        outline: none;
                        margin: 3rem auto;
                        display: block;
                        width: auto;
                        position: relative;
                        overflow: hidden;
                    }
                    .stButton > button::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(
                            90deg,
                            transparent,
                            rgba(255, 255, 255, 0.2),
                            transparent
                        );
                        transition: 0.5s;
                    }
                    .stButton > button:hover::before {
                        left: 100%;
                    }
                    .stButton > button:hover {
                        transform: scale(1.05);
                        box-shadow: 0 0 60px 20px rgba(0, 255, 204, 0.3);
                        color: #fff;
                    }
                    .loading-container {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 2rem 0;
                    }
                    .loading-text {
                        font-size: 1.2rem;
                        color: #00ffcc;
                        text-align: center;
                        margin-top: 1rem;
                        animation: pulse 1.5s ease-in-out infinite;
                    }
                    .progress-container {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(26, 26, 46, 0.95);
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        z-index: 1000;
                        backdrop-filter: blur(10px);
                    }
                    .progress-bar {
                        width: 80%;
                        max-width: 400px;
                        height: 6px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 3px;
                        overflow: hidden;
                        position: relative;
                    }
                    .progress-fill {
                        position: absolute;
                        top: 0;
                        left: 0;
                        height: 100%;
                        background: linear-gradient(90deg, #00ffcc, #00b4d8);
                        width: 0%;
                        transition: width 0.1s ease;
                        box-shadow: 0 0 20px rgba(0, 255, 204, 0.5);
                    }
                    .progress-text {
                        color: #00ffcc;
                        font-size: 1.5rem;
                        margin-top: 1rem;
                        text-align: center;
                        text-shadow: 0 0 10px rgba(0, 255, 204, 0.3);
                    }
                    .progress-percentage {
                        color: #fff;
                        font-size: 2rem;
                        font-weight: bold;
                        margin-top: 0.5rem;
                        text-shadow: 0 0 15px rgba(0, 255, 204, 0.5);
                    }
                    @keyframes pulse {
                        0% { opacity: 0.6; }
                        50% { opacity: 1; }
                        100% { opacity: 0.6; }
                    }
                    </style>
                """, unsafe_allow_html=True)

                st.markdown('<div class="big-title">Welcome to <span style="color:#00ffcc;">MedCare</span> Pharmacy</div>', unsafe_allow_html=True)
                
                # Enhanced subtitle with animations
                st.markdown('''
                    <div class="subtitle-container">
                        <div class="subtitle-line">Your <span class="subtitle-highlight">Trusted Partner</span> in Healthcare</div>
                        <div class="subtitle-line">Innovative Solutions for <span class="subtitle-highlight">Smart</span> Medication Management</div>
                        <div class="subtitle-line">Experience <span class="subtitle-highlight">Seamless</span> Healthcare Delivery</div>
                        <div class="subtitle-decoration"></div>
                    </div>
                ''', unsafe_allow_html=True)

                # Loading animation container
                st.markdown('<div class="loading-container">', unsafe_allow_html=True)
                lottie_animation = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_ktwnwv5m.json")
                st_lottie(lottie_animation, height=400, key="loading")
                st.markdown('<div class="loading-text">Initializing MedCare System...</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Feature cards row 1
                st.markdown('''
                <div class="feature-row-vfx">
                    <div class="feature-card-vfx">
                        <div class="feature-icon-vfx">💊</div>
                        <div class="feature-title-vfx">Smart Medicine Management</div>
                        <div class="feature-desc-vfx">Track and manage your medications with our intelligent dashboard. Get reminders and updates in real-time.</div>
                    </div>
                    <div class="feature-card-vfx">
                        <div class="feature-icon-vfx">📱</div>
                        <div class="feature-title-vfx">Digital Prescriptions</div>
                        <div class="feature-desc-vfx">Upload and manage your prescriptions digitally. Get instant verification and processing.</div>
                    </div>
                    <div class="feature-card-vfx">
                        <div class="feature-icon-vfx">🚚</div>
                        <div class="feature-title-vfx">Express Delivery</div>
                        <div class="feature-desc-vfx">Experience lightning-fast delivery with real-time tracking and instant updates.</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

                # Feature cards row 2
                st.markdown('''
                <div class="feature-row-vfx" style="margin-top:3rem;">
                    <div class="feature-card-vfx" style="min-width:600px; max-width:800px; width:100%;">
                        <div class="feature-title-vfx" style="font-size:2.2rem; text-align:center; margin-bottom:1.5rem;">Why Choose MedCare?</div>
                        <div class="why-row">
                            <div class="why-col">
                                <div class="why-item">
                                    <span class="why-icon">✨</span>
                                    <b>Intuitive Interface</b>
                                    <div class="why-desc">Experience a seamless, user-friendly design that makes managing your healthcare effortless.</div>
                                </div>
                                <div class="why-item">
                                    <span class="why-icon">🛡️</span>
                                    <b>Advanced Security</b>
                                    <div class="why-desc">Your medical data is protected with state-of-the-art encryption and security measures.</div>
                                </div>
                            </div>
                            <div class="why-col">
                                <div class="why-item">
                                    <span class="why-icon">⚡</span>
                                    <b>Lightning Fast</b>
                                    <div class="why-desc">Enjoy quick order processing and real-time updates for all your healthcare needs.</div>
                                </div>
                                <div class="why-item">
                                    <span class="why-icon">🤝</span>
                                    <b>24/7 Support</b>
                                    <div class="why-desc">Our dedicated support team is always ready to assist you with any queries or concerns.</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

                # Get Started button with progress animation
                if st.button("Get Started", use_container_width=False):
                    # Create a placeholder for the progress bar
                    progress_placeholder = st.empty()
                    
                    # Show progress container
                    progress_placeholder.markdown('''
                        <div class="progress-container">
                            <div class="progress-bar">
                                <div class="progress-fill" id="progressFill"></div>
                            </div>
                            <div class="progress-text">Preparing Your Experience</div>
                            <div class="progress-percentage">0%</div>
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    # Simulate progress
                    for i in range(101):
                        time.sleep(0.03)  # Adjust speed as needed
                        progress_placeholder.markdown(f'''
                            <div class="progress-container">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {i}%"></div>
                                </div>
                                <div class="progress-text">Preparing Your Experience</div>
                                <div class="progress-percentage">{i}%</div>
                            </div>
                        ''', unsafe_allow_html=True)
                    
                    # Clear progress and continue
                    progress_placeholder.empty()
                    st.session_state.show_welcome = False
                    st.rerun()
                return

        # Show logout button if logged in
        if st.session_state.logged_in or st.session_state.admin_logged_in or st.session_state.delivery_agent_logged_in:
            if st.sidebar.button("Logout", key="logout_btn"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.admin_logged_in = False
                st.session_state.delivery_agent_logged_in = False
                st.session_state.delivery_agent_phone = None
                st.rerun()

        # Admin panel
        if st.session_state.admin_logged_in:
            admin_panel()
        # Customer dashboard
        elif st.session_state.logged_in and st.session_state.username:
            customer_dashboard(st.session_state.username)
        # Delivery agent dashboard
        elif st.session_state.delivery_agent_logged_in and st.session_state.delivery_agent_phone:
            delivery_agent_dashboard(st.session_state.delivery_agent_phone)
        # Login/Signup/Billing
        else:
            # Main header with logo and title
            st.markdown('<div class="header">💊 Pharmacy Management System</div>', unsafe_allow_html=True)
            
            # Sidebar menu with icons
            menu_choice = st.sidebar.radio(
                "Menu",
                ["Customer", "Admin", "Delivery Agent", "Billing"],
                format_func=lambda x: f"👤 {x}" if x == "Customer" else 
                                    f"👨‍💼 {x}" if x == "Admin" else 
                                    f"🚚 {x}" if x == "Delivery Agent" else 
                                    f"💰 {x}"
            )

            if menu_choice == "Customer":
                st.markdown('<div class="subheader">👤 Customer Portal</div>', unsafe_allow_html=True)
                customer_choice = st.radio(
                    "Choose Action",
                    ["Login", "Sign Up"],
                    format_func=lambda x: f"🔑 {x}" if x == "Login" else f"📝 {x}"
                )
                
                if customer_choice == "Sign Up":
                    with st.form("signup_form"):
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Name*", placeholder="Enter your full name")
                            email = st.text_input("Email*", placeholder="example@email.com")
                            password = st.text_input("Password*", type='password')
                            confirm_password = st.text_input("Confirm Password*", type='password')
                        with col2:
                            state = st.text_input("State*", placeholder="Your state")
                            number = st.text_input("Phone Number*", placeholder="+91XXXXXXXXXX")
                            ssn = st.text_input("SSN (Optional)", placeholder="XXX-XX-XXXX")

                        # Insurance selection
                        try:
                            cursor = db_manager.get_cursor()
                            if cursor:
                                cursor.execute('SELECT InsuranceID, CompName FROM Insurance')
                                insurances = cursor.fetchall()
                                insurance_options = ["None"] + [f"{ins[0]} - {ins[1]}" for ins in insurances]
                                selected_insurance = st.selectbox("Select Insurance (Optional)", insurance_options)

                                insurance_id = None
                                if selected_insurance != "None":
                                    insurance_id = int(selected_insurance.split(" - ")[0])
                        except mysql.connector.Error as err:
                            st.error(f"Error loading insurance options: {err}")
                            insurance_id = None

                        submitted = st.form_submit_button("Sign Up")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if submitted:
                            if not all([name, email, password, state, number]):
                                st.error("Please fill all required fields (marked with *)")
                            elif password != confirm_password:
                                st.error("Passwords do not match!")
                            elif not email_valid(email):
                                st.error("Please enter a valid email address")
                            elif not validate_phone(number):
                                st.error("Please enter a valid phone number")
                            elif ssn and not validate_ssn(ssn):
                                st.error("SSN should be in format XXX-XX-XXXX")
                            else:
                                if customer_add_data(name, password, email, state, number, ssn if ssn else None, insurance_id):
                                    st.success("Account created successfully! Please log in.")
                                    st.balloons()
                                    st.rerun()
                
                else:  # Login
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    login_tab, forgot_password_tab = st.tabs(["🔑 Login", "🔓 Forgot Password"])
                    
                    with login_tab:
                        with st.form("login_form"):
                            username = st.text_input("Username", placeholder="Enter your username")
                            password = st.text_input("Password", type='password', placeholder="Enter your password")

                            submitted = st.form_submit_button("Login")
                            if submitted:
                                if username and password:
                                    if get_authenticate(username, password):
                                        st.session_state.logged_in = True
                                        st.session_state.username = username
                                        st.success("Login successful!")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error("Invalid Credentials")
                                else:
                                    st.warning("Please enter username and password")
                    
                    with forgot_password_tab:
                        with st.form("forgot_password_form"):
                            phone = st.text_input("Enter your registered phone number", placeholder="+91XXXXXXXXXX")
                            new_password = st.text_input("New Password", type='password')
                            confirm_password = st.text_input("Confirm New Password", type='password')
                            
                            submitted = st.form_submit_button("Reset Password")
                            if submitted:
                                if not phone:
                                    st.error("Please enter your phone number")
                                elif not validate_phone(phone):
                                    st.error("Please enter a valid phone number")
                                elif not new_password or not confirm_password:
                                    st.error("Please enter and confirm your new password")
                                elif new_password != confirm_password:
                                    st.error("Passwords do not match")
                                else:
                                    if reset_customer_password(phone, new_password):
                                        st.success("Password reset successful! Please login with your new password.")
                                        st.balloons()
                                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            elif menu_choice == "Admin":
                st.markdown('<div class="subheader">👨‍💼 Admin Portal</div>', unsafe_allow_html=True)
                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("admin_login_form"):
                    admin_username = st.text_input("Admin Username", placeholder="Enter admin username")
                    admin_password = st.text_input("Admin Password", type='password', placeholder="Enter admin password")
                    
                    submitted = st.form_submit_button("Login as Admin")
                    if submitted:
                        if admin_username == 'admin' and admin_password == 'admin':
                            st.session_state.admin_logged_in = True
                            st.success("Admin login successful!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Invalid Admin Credentials")
                st.markdown('</div>', unsafe_allow_html=True)

            elif menu_choice == "Delivery Agent":
                st.markdown('<div class="subheader">🚚 Delivery Agent Portal</div>', unsafe_allow_html=True)
                agent_choice = st.radio(
                    "Choose Action",
                    ["Login", "Sign Up"],
                    format_func=lambda x: f"🔑 {x}" if x == "Login" else f"📝 {x}"
                )
                
                if agent_choice == "Sign Up":
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    with st.form("delivery_agent_signup"):
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Name", placeholder="Enter your full name")
                            phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
                            password = st.text_input("Password", type='password')
                        with col2:
                            address = st.text_area("Address", placeholder="Enter your complete address")
                        
                        submitted = st.form_submit_button("Sign Up")
                        if submitted:
                            if not all([name, phone, password, address]):
                                st.error("Please fill all fields")
                            elif not validate_phone(phone):
                                st.error("Please enter a valid phone number")
                            else:
                                if delivery_agent_add_data(name, phone, password, address):
                                    st.success("Account created successfully! Please log in.")
                                    st.balloons()
                                    st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:  # Login
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    with st.form("delivery_agent_login"):
                        phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
                        password = st.text_input("Password", type='password')
                        
                        submitted = st.form_submit_button("Login")
                        if submitted:
                            if phone and password:
                                if delivery_agent_authenticate(phone, password):
                                    st.session_state.delivery_agent_logged_in = True
                                    st.session_state.delivery_agent_phone = phone
                                    st.success("Login successful!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("Invalid Credentials")
                            else:
                                st.warning("Please enter phone number and password")
                    st.markdown('</div>', unsafe_allow_html=True)

            elif menu_choice == "Billing":
                st.markdown('<div class="subheader">💰 Billing Portal</div>', unsafe_allow_html=True)
                st.markdown('<div class="card">', unsafe_allow_html=True)

                # Initialize billing cart in session state
                if 'billing_cart' not in st.session_state:
                    st.session_state.billing_cart = {}
                if 'show_bill_summary' not in st.session_state:
                    st.session_state.show_bill_summary = False
                if 'bill_items' not in st.session_state:
                    st.session_state.bill_items = []
                if 'bill_total' not in st.session_state:
                    st.session_state.bill_total = 0

                with st.form("billing_form"):
                    phone = st.text_input("Customer Phone Number", placeholder="+91XXXXXXXXXX")
                    search_term = st.text_input("Search Medicine", placeholder="Enter medicine name")

                    drugs = drug_view_all_data()
                    filtered_drugs = [drug for drug in drugs 
                                     if search_term.lower() in drug[0].lower() 
                                     and drug[3] > 0]  # Only show available drugs

                    qty_inputs = {}
                    if filtered_drugs:
                        st.subheader("Available Medicines")
                        for drug in filtered_drugs:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"**{drug[0]}** (Available: {drug[3]})")
                                st.write(f"Use: {drug[2]}")
                            with col2:
                                price = float(drug[5]) if drug[5] is not None else 0
                                st.write(f"Price: ₹{price:.2f}")
                            with col3:
                                qty = st.number_input("Qty", 0, drug[3], key=f"bill_{drug[4]}")
                                qty_inputs[drug[4]] = {
                                    'drug_id': drug[4],
                                    'drug_name': drug[0],
                                    'quantity': qty,
                                    'unit_price': price
                                }

                    submitted = st.form_submit_button("Generate Bill")
                    if submitted:
                        if not phone:
                            st.error("Please enter customer phone number")
                        else:
                            # Build the cart from all selected quantities > 0
                            st.session_state.billing_cart = {}
                            for drug_id, item in qty_inputs.items():
                                if item['quantity'] > 0:
                                    item['subtotal'] = item['quantity'] * item['unit_price']
                                    st.session_state.billing_cart[drug_id] = item
                            if not st.session_state.billing_cart:
                                st.error("Please add at least one medicine to the bill")
                            else:
                                # Prepare bill summary
                                bill_items = []
                                total = 0
                                for item in st.session_state.billing_cart.values():
                                    bill_items.append(item)
                                    total += item['subtotal']
                                st.session_state.bill_items = bill_items
                                st.session_state.bill_total = total
                                st.session_state.show_bill_summary = True

                # Show bill summary and confirm bill
                if st.session_state.show_bill_summary:
                    st.subheader("Bill Summary")
                    if st.session_state.bill_items:
                        import pandas as pd
                        df = pd.DataFrame(st.session_state.bill_items)
                        df = df[['drug_name', 'quantity', 'unit_price', 'subtotal']]
                        df.columns = ['Medicine', 'Quantity', 'Unit Price', 'Subtotal']
                        st.dataframe(df)
                        st.write(f"**Total Amount:** ₹{st.session_state.bill_total:.2f}")
                        if st.button("Confirm Bill"):
                            bill_id = create_bill(phone, st.session_state.bill_items)
                            if bill_id:
                                st.success(f"Bill #{bill_id} generated successfully!")
                                st.balloons()
                                st.session_state.billing_cart = {}
                                st.session_state.show_bill_summary = False
                                st.session_state.bill_items = []
                                st.session_state.bill_total = 0
                            else:
                                st.error("Failed to generate bill. Please try again.")
                        if st.button("Cancel Bill"):
                            st.session_state.show_bill_summary = False
                            st.session_state.bill_items = []
                            st.session_state.bill_total = 0
                    else:
                        st.info("No items in bill.")

                # Show current cart
                if st.session_state.billing_cart and not st.session_state.show_bill_summary:
                    st.subheader("Current Bill Cart")
                    total = 0
                    for item in st.session_state.billing_cart.values():
                        st.write(f"{item['drug_name']} - Qty: {item['quantity']} × ₹{item['unit_price']:.2f} = ₹{item['subtotal']:.2f}")
                        total += item['subtotal']
                        if st.button(f"Remove {item['drug_name']}", key=f"remove_bill_{item['drug_id']}"):
                            del st.session_state.billing_cart[item['drug_id']]
                            st.experimental_rerun()
                    st.write(f"**Total (Current Cart): ₹{total:.2f}")

                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
    finally:
        db_manager.close()

if __name__ == '__main__':
    main()
