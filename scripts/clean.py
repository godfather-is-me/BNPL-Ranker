import os
import utils as u

from pyspark.sql import SparkSession
from pyspark.sql.types import FloatType
from pyspark.sql.functions import col, round, monotonically_increasing_id

class Clean():
    """
    Class dedicated for cleaning internal and external datasets
    """

    def __init__(self):
        self.sp = (
            SparkSession.builder.appName("Clean BNPL")
            .config("spark.sql.session.timeZone", "+11")
            .getOrCreate()
        )
        self.user_lookup = u.read_tables(self.sp, "consumer_user_details")
        self.transactions = u.read_tables(self.sp, "transactions")
        self.consumer = u.read_tables(self.sp, "tbl_consumer","c")
        self.c_fraud = u.read_tables(self.sp, "consumer_fraud_probability" , "c")
        self.m_fraud = u.read_tables(self.sp, "consumer_fraud_probability", "c")
       

    def __del__(self):
        self.sp.stop
        print("Clean Up Completed!")

    def clean_all(self):
        """
        Function to clean all code and output into the curated data folder
        """
        
        # Call list of cleaning functions
        self.transform_consumer_id()
        self.dollar_value()
        self.drop_cols()
        self.convert_data()

        # Write final data into curated folder
        self.write_all()
        
    def transform_consumer_id(self):
        """
        Merely change consumer_id in all datasets to user_id, by changing the consumer fraud and 
        consumer dataframes.
        """
        self.consumer = self.consumer.join(self.user_lookup, on="consumer_id")
        self.consumer = self.consumer.drop("consumer_id")
        
        
        
    def clean_tax_income(self):
        # Update to include tax income data (EXAMPLE ONLY)
        tax_income = u.read_tables(self.sp, "tax_income", "c")
        pass

    def dollar_value(self):
        """
        Function to clean dollar values and remove the noise associated with the data
        """
        # round each transaction to the nearest cent
        self.transactions = self.transactions.withColumn("dollar_value", round(col("dollar_value"), 2))
        self.transactions = self.transactions.withColumn("dollar_value", col("dollar_value").cast(FloatType()))

    def drop_cols(self):
        """
        Function to drop unnecessary columns
        """
        # Replace order_id with index
        self.transactions = self.transactions.drop("order_id")
        self.transactions = self.transactions.withColumn("order_id", monotonically_increasing_id())

    def convert_data(self):
        """
        Function to convert datatypes of the following probabilites
            - Convert fraud probabilites column from string to float
        """
        self.c_fraud = self.c_fraud.withColumn("fraud_probability", col("fraud_probability").cast(FloatType()))
        self.m_fraud = self.m_fraud.withColumn("fraud_probability", col("fraud_probability").cast(FloatType()))

    def write_all(self):
        """
        Function to write all cleaned data into curated
        """
        folder = "curated"

        # Files to write
        u.write_data(self.transactions, folder, "transactions")
        u.write_data(self.c_fraud, folder, "customer_fraud")
        u.write_data(self.m_fraud, folder, "merchant_fraud")
        u.write_data(self.consumer, folder, "consumer")
        print("Files have been written")

cleaner = Clean()
cleaner.clean_all()
