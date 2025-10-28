# Import the QueryBase class
from .query_base import QueryBase

# Import dependencies needed for sql execution
# from the `sql_execution` module
from .sql_execution import QueryMixin


# Define a subclass of QueryBase
# called Employee
class Employee(QueryBase, QueryMixin):

    # Set the class attribute `name`
    # to the string "employee"
    name = "employee"


    # Define a method called `names`
    # that receives no arguments
    # This method should return a list of tuples
    # from an sql execution
    def names(self):

        # Query 3
        # Write an SQL query
        # that selects two columns
        # 1. The employee's full name
        # 2. The employee's id
        # This query should return the data
        # for all employees in the database
        sql_query = """
            SELECT (first_name || ' ' || last_name) AS full_name,
                   employee_id
            FROM employee
        """
        return self.query(sql_query)
    
    # Define a method called `username`
    # that receives an `id` argument
    # This method should return a list of tuples
    # from an sql execution
    def username(self, id):

        # Query 4
        # Write an SQL query
        # that selects an employees full name
        # Use f-string formatting and a WHERE filter
        # to only return the full name of the employee
        # with an id equal to the id argument
        sql_query = f"""
            SELECT (first_name || ' ' || last_name) AS full_name
            FROM employee
            WHERE employee_id = {id}
        """
        return self.query(sql_query)
    

    # Below is method with an SQL query
    # This SQL query generates the data needed for
    # the machine learning model.
    # Without editing the query, alter this method
    # so when it is called, a pandas dataframe
    # is returns containing the execution of
    # the sql query

    def model_data(self, id):

        return f"""
                    SELECT SUM(positive_events) positive_events
                         , SUM(negative_events) negative_events
                    FROM {self.name}
                    JOIN employee_events
                        USING({self.name}_id)
                    WHERE {self.name}.{self.name}_id = {id}
                """
