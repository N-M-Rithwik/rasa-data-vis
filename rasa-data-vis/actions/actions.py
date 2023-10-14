# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List
import collections

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import sqlite3
from fuzzywuzzy import process
import matplotlib.pyplot as plt
import seaborn as sns
import csv

class ReadActionCSVFiles(Action):
    def name(self):
        return "action_read_csvFiles"

    def run(self, dispatcher, tracker, domain):
        # Define the paths to CSV files
        test_case_file_path = "/Users/nmrithwik/rasa-data-vis/tcDb/testCasesData.csv"
        test_execution_file_path = "/Users/nmrithwik/rasa-data-vis/tcDb/testExecutionData.csv"

        # Creating a connection to the database
        conn = DbQueryingMethods.create_connection(db_file="/Users/nmrithwik/rasa-data-vis/tcDb/qa_database.db")

        cursor = conn.cursor()

        # Define the table schema and create the table if it does not exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS Test_Execution (
                            TestCaseName TEXT,
                            TestCaseId INTEGER,
                            TestType TEXT,
                            GroupName TEXT,
                            AppName TEXT,
                            Status TEXT
                        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Test_Case (
                            TestCaseName TEXT,
                            TestCaseId INTEGER,
                            TestType TEXT,
                            GroupName TEXT
                        )''')
        
        # Insert the values into Test Execution table if it is empty
        query = "SELECT COUNT(*) FROM Test_Execution"
        cursor.execute(query)
        row_count = cursor.fetchone()[0]
        if row_count == 0:
            with open(test_execution_file_path, 'r') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Skip the header row if it exists
                for row in csv_reader:
                    cursor.execute('INSERT INTO Test_Execution VALUES (?, ?, ?, ?, ? ,?)', row)
        else:
            print("The table is not empty")

        # Insert the values into Test Case table if it is empty
        query = "SELECT COUNT(*) FROM Test_Case"
        cursor.execute(query)
        row_count = cursor.fetchone()[0]
        if row_count == 0:
            with open(test_case_file_path, 'r') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Skip the header row if it exists
                for row in csv_reader:
                    cursor.execute('INSERT INTO Test_Case VALUES (?, ?, ?, ?)', row)
        else:
            print("The table is not empty")

        dispatcher.utter_message(text="Database has been updated.")

        conn.commit()
        conn.close()

        return []


class ActionDisplayTable(Action):
    def name(self) -> Text:
        return "action_display_table"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        conn = DbQueryingMethods.create_connection(db_file="/Users/nmrithwik/rasa-data-vis/tcDb/qa_database.db")

        slot_value = tracker.get_slot("table_name")
        slot_value = DbQueryingMethods.get_table_name(slot_value=slot_value)

        # Fetch all the rows from the query result
        rows = DbQueryingMethods.get_table_details(conn=conn, slot_value=slot_value)

        # Print or process the rows
        for row in rows:
            dispatcher.utter_message(text=str(row))

        conn.close()
        return []
    
class ActionDeleteTable(Action):
    def name(self) -> Text:
        return "action_delete_table"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        conn = DbQueryingMethods.create_connection(db_file="/Users/nmrithwik/rasa-data-vis/tcDb/qa_database.db")

        slot_value = tracker.get_slot("table_name")
        slot_value = DbQueryingMethods.get_table_name(slot_value=slot_value)

        # Fetch all the rows from the query result
        DbQueryingMethods.delete_table(conn=conn, slot_value=slot_value)
        dispatcher.utter_message(text="Deleted Table " + slot_value)

        conn.close()
        return []
    
class DbQueryingMethods:

    # Create connection
    def create_connection(db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except sqlite3.Error as e:
            print(e)
        return conn
    
    # Get Table Name
    def get_table_name(slot_value):
        if "case" in slot_value :
            slot_value = "Test_Case"
        else :
            slot_value = "Test_Execution"
        return slot_value
    
    # Display table details
    def get_table_details(conn, slot_value):
        cur = conn.cursor()
        cur.execute(f'''SELECT * FROM {slot_value}
                    ''')
        rows = cur.fetchall()
        return(rows)
    
    # Delete Table
    def delete_table(conn, slot_value):
        cur = conn.cursor()
        cur.execute(f'''DROP TABLE {slot_value}
                    ''')
        return

    # Get a list of all distinct values from our target column
    def get_distinct_values(conn, slot_value):
        cur = conn.cursor()
        cur.execute(f'''SELECT DISTINCT {slot_value} 
                    FROM Test_Execution''')
        column_values = cur.fetchall()
        new_list = [item[0] for item in column_values]
        return(new_list)
    
    # Get the count of items in table
    def get_count(conn, slot_value, categories):
        values = []
        for name in categories:
            cur = conn.cursor()
            cur.execute(f'''SELECT COUNT(*) FROM Test_Execution
                        WHERE {slot_value}="{name}"''')
            values.append(cur.fetchall())
        new_list = [item[0] for item in values]
        return(new_list)
    
    # Get the appropriate column name
    def get_column_name(slot_value):
        if "id" in slot_value :
            slot_value = "TestCaseId"
        elif "case" in slot_value :
            slot_value = "TestCaseName"
        elif "group" in slot_value :
            slot_value = "GroupName"
        elif "type" in slot_value :
            slot_value = "TestType"
        elif "app" in slot_value :
            slot_value = "AppName"
        else :
            slot_value = "Status"
        return slot_value
    
class DisplayActionBarChart(Action):
    def name(self):
        return "action_display_barChart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        conn = DbQueryingMethods.create_connection(db_file="/Users/nmrithwik/rasa-data-vis/tcDb/qa_database.db")
        slot_value = tracker.get_slot("column_name")
        slot_value = DbQueryingMethods.get_column_name(slot_value)

        # Fetching different categories and their values
        categories = DbQueryingMethods.get_distinct_values(conn=conn, slot_value=slot_value)
        values = DbQueryingMethods.get_count(conn=conn, slot_value=slot_value, categories=categories)
        value_list = [item[0] for item in values]

        # Create a bar chart
        colors = sns.color_palette('pastel', len(categories))

        plt.bar(categories, value_list, color=colors)

        # Add title and labels
        plt.title('Bar Chart')
        plt.xlabel(slot_value)
        plt.ylabel('Values')

        # Display the chart
        dispatcher.utter_message(image=plt.show())
        return []
    
class DisplayActionPieChart(Action):
    def name(self):
        return "action_display_pieChart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        conn = DbQueryingMethods.create_connection(db_file="/Users/nmrithwik/rasa-data-vis/tcDb/qa_database.db")
        slot_value = tracker.get_slot("column_name")
        slot_value = DbQueryingMethods.get_column_name(slot_value)

        # Fetching different categories and their values
        categories = DbQueryingMethods.get_distinct_values(conn=conn, slot_value=slot_value)
        values = DbQueryingMethods.get_count(conn=conn, slot_value=slot_value, categories=categories)
        value_list = [item[0] for item in values]

        # Create a pie chart
        colors = sns.color_palette('pastel', len(categories))
        plt.pie(value_list, labels=categories, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.title(f"Distribution of {slot_value}")
        plt.axis('equal')

        # Display the chart
        dispatcher.utter_message(image=plt.show())
        return []
    
class DisplayActionDonutChart(Action):
    def name(self):
        return "action_display_donutChart"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        conn = DbQueryingMethods.create_connection(db_file="/Users/nmrithwik/rasa-data-vis/tcDb/qa_database.db")
        slot_value = tracker.get_slot("column_name")
        slot_value = DbQueryingMethods.get_column_name(slot_value)

        # Fetching different categories and their values
        categories = DbQueryingMethods.get_distinct_values(conn=conn, slot_value=slot_value)
        values = DbQueryingMethods.get_count(conn=conn, slot_value=slot_value, categories=categories)
        value_list = [item[0] for item in values]

        # Create a donut chart
        fig, ax = plt.subplots()
        ax.pie(value_list, labels=categories, autopct='%1.1f%%', startangle=90, pctdistance=0.85, wedgeprops=dict(width=1.0))
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        fig.gca().add_artist(centre_circle)
        ax.axis('equal')  
        plt.title(f"Donut Chart {slot_value}")

        # Show the chart
        plt.tight_layout()
        dispatcher.utter_message(image=plt.show())
        return []