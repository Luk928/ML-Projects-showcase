# -*- coding: utf-8 -*-
"""
@author: Łukasz Ozimek
"""
import argparse
import pandas as pd
import mysql.connector
from getpass import getpass
import sys
# Server low level functions:

def connect_to_localhost():
    # Connecting to localhost with user input
    mydb = mysql.connector.connect(
        host="localhost",
        user=input("Enter username: "),
        password=getpass("Enter password: "))
    return mydb, mydb.cursor()
    
def show_database_list(cursor):
    # Show database list
    query = 'SHOW DATABASES'
    cursor.execute(query)
    print('Databse list:')
    for db in cursor:
        print(db)
    
def create_database(db_name, cursor):
    # Function to create database
    try:
        query = 'CREATE DATABASE ' + db_name
        cursor.execute(query)
    except:
        # Deleting databse if it already exists
        query = 'DROP DATABASE ' + db_name
        cursor.execute(query)
        query = 'CREATE DATABASE ' + db_name
        cursor.execute(query)

# Database low level functions:

def connect_to_database(db_name):
    # Connecting to localhost database with user input
    mydb = mysql.connector.connect(
        host="localhost",
        user=input("Enter username: "),
        password=getpass("Enter password: "),
        database = db_name)
    return mydb, mydb.cursor() # Returns database connector and cursor

def show_table_list(cursor):
    # Show list of tables in database
    query="SHOW TABLES"
    cursor.execute(query)
    print('Table list:')
    for tb in cursor:
        print(tb)
    
def df_to_query(table, dataframe):
    # Function to turn a dataframe into a SQL query (pandas to_sql() function doesn't work with mysql.connector)
    query = "INSERT INTO "+table+" ("
    string = ''
    for i in dataframe.columns:
        string = string + i+','
    string = string[0:-1]
    query = query+string+') VALUES'
    str_list = []
    for i in range(0,dataframe.shape[0]):
        str2 = ''
        df_row = dataframe[i:i+1]
        vals=df_row.values.tolist()[0]
        for val in vals:
            if type(val)==str:
                str2 = str2+"\""+val+"\","
            else:
                str2 = str2+str(val)+','
        str_list.append(str2)

    for idx,item in enumerate(str_list):
        str_list[idx] = '('+item[0:-1]+')'

    for i in str_list:
        query = query+i+','
    query = query[0:-1]
    return query

def initialize_tables(db_connector, cursor):
    # Function to initialize tables with sample data
    
    # Deleting the tables if they already exist
    try:
        query = "DROP TABLE projects"
        cursor.execute(query)
        query = "DROP TABLE employees"
        cursor.execute(query)
        query = "DROP TABLE clients"
        cursor.execute(query)
    except:
        pass
    
    query = """
    CREATE TABLE employees(
        emp_id INT PRIMARY KEY,
        name VARCHAR(30),
        last_name VARCHAR(30),
        age INT,
        salary INT
    )
    """
    cursor.execute(query)
    db_connector.commit()
        
    
    # Creating the clients table
    query = """
    CREATE TABLE clients(
        client_id INT PRIMARY KEY,
        client_name VARCHAR(30)
    )
    """
    cursor.execute(query)
    db_connector.commit()
    
    # Creating the projects table
    query = """
    CREATE TABLE projects(
        emp_id INT,
        client_id INT,
        price INT,
        PRIMARY KEY(emp_id,client_id),
        FOREIGN KEY(emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
        FOREIGN KEY(client_id) REFERENCES clients(client_id) ON DELETE CASCADE
    )
    """
    cursor.execute(query)
    db_connector.commit()
    
    # Creating sample data for the tables    
    employees = {
        'emp_id':[23435,75536,78646,43235],
        'name':['John','Jane','Michael','Michelle'],
        'last_name':['Smith','Doe','Kane','Solo'],
        'age':[43,25,35,51],
        'salary':[100000,40000,60000,120000]
    }
    
    clients = {
        'client_id':[235546,667785,334432,675896,333577],
        'client_name':['Facebook','Amazon','Netflix','Google','Some company']
    }
    
    projects = {
        'client_id':[235546,667785,334432,675896,333577],
        'emp_id':[23435,75536,78646,43235,23435],
        'price':[10000,4500,80000,34000,10000]
    }
    
    # Converting dictioniaries to dataframes
    emp_df = pd.DataFrame.from_dict(employees) 
    client_df = pd.DataFrame.from_dict(clients)
    project_df = pd.DataFrame.from_dict(projects)
    
    table_names = ['employees', 'clients', 'projects']
    dataframes = [emp_df, client_df, project_df]
    for idx, item in enumerate(table_names):
        query = df_to_query(item, dataframes[idx])
        cursor.execute(query)
        db_connector.commit()
        
def show_table(cursor, table_name):
    # Function to show all data from table
    query = "SELECT * FROM " + table_name
    cursor.execute(query)
    result = cursor.fetchall()
    for x in result:
        print(x)
        
def show_column_names(cursor, table_name):
    cursor.execute("SHOW columns FROM " +table_name)
    print([column[0] for column in cursor.fetchall()])
    
def print_results(result):
    # Function to print results
    for x in result:
        print(x)
    
def show_and_order(cursor, table_name, col_name):
    # Selecting all elements and ordering by specified column
    query = "SELECT * FROM " + table_name +" ORDER BY " + col_name
    cursor.execute(query)
    result = cursor.fetchall()
    print_results(result)
        
def show_distinct(cursor, table_name, col_name):
    # Selecting distinct values from projects
    query = "SELECT DISTINCT " + col_name + " FROM "+table_name
    cursor.execute(query)
    result = cursor.fetchall()
    print_results(result)
        
def show_employees_over_salary(cursor, salary):
    # Counting emloyees over 30 with salary bigger than 70000
    query = "SELECT COUNT(emp_id) FROM employees WHERE salary>"+str(salary)
    cursor.execute(query)
    result = cursor.fetchall()
    print_results(result)
    
def show_average_value(cursor, table_name, col_name):
    # Getting the average project price
    query = "SELECT AVG(" + col_name + ") FROM " + table_name
    cursor.execute(query)
    result = cursor.fetchall()
    print_results(result)

def show_project_list(cursor):
    # Query to select names of employees and clients related to all projects
    query = """
    SELECT employees.name, employees.last_name, clients.client_name, projects.price
    FROM projects
    JOIN employees ON employees.emp_id=projects.emp_id
    JOIN clients ON clients.client_id=projects.client_id
    """
    cursor.execute(query)
    result = cursor.fetchall()
    print_results(result)
    

def add_employee(db_connector, cursor, emp_id, name, last_name,age,salary):
    # A function to allow a user to add employees    
    query = """
    INSERT INTO employees(emp_id, name, last_name, age, salary)
    VALUES (%s, %s, %s, %s, %s)
    """ % (emp_id, name, last_name, age, salary)
    cursor.execute(query)
    db_connector.commit()
    
    
    
# High level functions:

def server_level(db_name):
    # Function to call server level functions
    user_input = ''
    db_connector, cursor = connect_to_localhost()
    show_database_list(cursor)
    while user_input not in ['y','n']:
        user_input = input('Create the ' + db_name + ' database? [y/n]')
    if user_input == 'y':
        create_database(db_name, cursor)
        show_database_list(cursor)
    
def database_interface(db_name):
    # Function to open the database interface
    user_input = ''
    db_connector, cursor = connect_to_database(db_name)
    while user_input not in ['y','n']:
        user_input = input('Initialize the tables? [y/n]')
    if user_input == 'y':
        initialize_tables(db_connector, cursor)
    show_table_list(cursor)
    
    
    # Opening the interface:
    while user_input != 'quit':
        user_input = input("""Type in a command, 'help' to see the command list
                           or 'quit' to exit the interface: """)
        help_text = """
        The commands ask for arguments after they are called.\n\n
        Available commands: \n
        \t show_table_list - shows list of all tables \n
        \t show_table - shows specified table \n
        \t show_column_names - shows names of columns in specified table \n
        \t show_and_order - shows values in specified table ordered by specified column value \n
        \t show_distinct - shows distinct values in specified column in specified table \n
        \t show_employees_over_salary - shows number of employees with salary over specified amount \n
        \t show_average_value - shows average value in specified column in specified table \n
        \t show_project_list - shows all projects and details about the client and employee \n
        \t add_employee - adds an employee to the correct table \n
        """
    
    # Interface command:
        # help command
        if user_input=='help':
            print(help_text)
            
        elif user_input=='show_table_list':
            show_table_list(cursor)
            
        # show_table command
        elif user_input=='show_table':
            table_name = input('Input the table name: ')
            try:            
                print('\t', table_name, ' table: \n')
                show_column_names(cursor, table_name)
                show_table(cursor, table_name)
            except:
                print('Table not found')
        
        # show_column_names command
        elif user_input=='show_column_names':
            table_name = input('Input the table name: ')
            try:
                print('Column names:')
                show_column_names(cursor, table_name)
            except:
                print('Table not found')
        
        # show_and_order command
        elif user_input=='show_and_order':
            table_name = input('Input the table name: ')
            col_name = input('Input the column name: ')
            try:
                print('Results:')
                show_column_names(cursor, table_name)
                show_and_order(cursor, table_name, col_name)
            except:
                print('Wrong column or table name')
                
        # show_distinct command
        elif user_input=='show_distinct':
            table_name = input('Input the table name: ')
            col_name = input('Input the column name: ')
            try:
                show_distinct(cursor, table_name, col_name)
            except:
                print('Wrong column or table name')
        
        # show_employees_over_salary command
        elif user_input=='show_employees_over_salary':
            salary = input('Input the salary: ')
            try:
                salary = int(salary)
                show_employees_over_salary(cursor, salary)
            except:
                print('Salary must be a number')
        
        # show_average_value command
        elif user_input=='show_average_value':
            table_name = input('Input the table name: ')
            col_name = input('Input the column name: ')
            try:
                show_average_value(cursor, table_name, col_name)
            except:
                print('Wrong column or table name')
        
        # show_project_list command
        elif user_input=='show_project_list':
            show_project_list(cursor)
        
        # add_employee command
        elif user_input=='add_employee':
            # Downloading list of employee IDs to ensure the new one is unique
            query = "SELECT emp_id FROM employees"
            cursor.execute(query)
            results = cursor.fetchall()
            data_checker = True # Boolean value used for validation
            
            # Argument collection and validation
                # ID:
            emp_id = input('Input new employee ID: ')
            try:
                emp_id = int(emp_id)
                if emp_id<10000 or emp_id > 99999:
                    print('Employee ID must have 5 digits')
                    data_checker = False
                if (emp_id,) in results:
                    print('Employee ID must be unique')
                    data_checker = False
            except:
                print('Employee ID must be a number')
                data_checker = False
            
            if data_checker:
                # Name:
                name = input('Input new employee name: ')
                if len(name)<2 or len(name) > 30:
                    print('Employee name must be between 2-30 characters')
                    data_checker = False
                else:
                    name = '\"'+name+'\"'
            
            if data_checker:
                # Last name:
                last_name = input('Input new employee last name: ')
                if len(last_name)<2 or len(last_name) > 30:
                    print('Employee name must be between 2-30 characters')
                    data_checker = False
                last_name = '\"'+last_name+'\"'
            
            if data_checker:
                # Age
                age = input('Input new employee age: ')
                try:
                    age = int(age)
                    if age<10 or age > 200:
                        print('Employee must be 10-200 years old')
                        data_checker = False
                except:
                    print('Age must be a number')
                    data_checker = False
                    
            if data_checker:
                # Salary
                salary = input('Input new employee salary: ')
                try:
                    salary = int(salary)
                    if salary<1000:
                        print('Salary must be higher than 1000')
                        data_checker = False
                except:
                    print('Salary must be a number')
                    data_checker = False
                    
            # If all data is correct the function will run
            if data_checker:
                add_employee(db_connector, cursor, emp_id, name, last_name,age,salary)
                print('Employee added')
        
        
def main():
    parser = argparse.ArgumentParser(
        description='''MySQL Python project.''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(help='Sub-commands', dest='command')
    
    parser_generate_images = subparsers.add_parser('server_level', help='Server level functinos')
    parser_generate_images.add_argument('--db_name', help='Name of the database to be created', required=True)
    
    
    parser_generate_images = subparsers.add_parser('database_interface', help='Run the database interface')
    parser_generate_images.add_argument('--db_name', help='Name of the database to connect to', required=True)
    
    
    args = parser.parse_args()
    kwargs = vars(args)
    subcmd = kwargs.pop('command')
    if subcmd is None:
        print ('Error: missing subcommand.')
        sys.exit(1)
    elif subcmd == 'server_level':
        server_level(**kwargs)
    elif subcmd == 'database_interface':
        database_interface(**kwargs)
    
if __name__ == "__main__":
    main()