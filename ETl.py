import csv
import io
import boto3

s3 = boto3.client('s3')

def lambda_handler(event, context):

    bucket_name = 'superstore-analytics-prem-2026'
    
    # 1. CSV read from S3
    response = s3.get_object(Bucket=bucket_name, Key='input/sales_data.csv')
    content = response['Body'].read().decode('utf-8-sig')  # utf-8-sig removes invisible BOM characters
    lines = content.splitlines()
    
    reader = csv.DictReader(lines)
    
    # 2. Aggregation: (Category, Region) -> Sales, Profit, Orders
    summary = {}
    for raw_row in reader:
        # Strip whitespace and lowercase all column keys
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        
        cat = row.get('category', 'Unknown')
        reg = row.get('region', 'Unknown')
        
        try:
            sales = float(row.get('sales', 0))
        except ValueError:
            sales = 0.0
            
        try:
            profit = float(row.get('profit', 0))
        except ValueError:
            profit = 0.0
        
        key = (cat, reg)
        if key not in summary:
            summary[key] = {'Total_Sales': 0.0, 'Total_Profit': 0.0, 'Total_Orders': 0}
            
        summary[key]['Total_Sales'] += sales
        summary[key]['Total_Profit'] += profit
        summary[key]['Total_Orders'] += 1

    # 3. prepare output on  CSV format
    output_buffer = io.StringIO()
    writer = csv.writer(output_buffer)
    writer.writerow(['Category', 'Region', 'Total_Sales', 'Total_Profit', 'Total_Orders'])
    
    for (cat, reg), data in summary.items():
        writer.writerow([
            cat, 
            reg, 
            round(data['Total_Sales'], 2), 
            round(data['Total_Profit'], 2), 
            data['Total_Orders']
        ])
    
    # 4. save on Output folder
    s3.put_object(
        Bucket=bucket_name,
        Key='output/sales_summary.csv',
        Body=output_buffer.getvalue()
    )
    
    return {
        'statusCode': 200,
        'body': 'Sales summary successfully generated and stored in output folder!'
    }
