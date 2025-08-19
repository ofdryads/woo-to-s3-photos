# Woo-to-S3 Product Photos
Convert photos from WooCommerce/WordPress to .webp and migrate them to an AWS S3 bucket. This can help you migrate your eCommerce website off of WordPress and onto another platform, or improve performance on your current website.
- Download all the product photos for your entire product catalog, organizing them in folders by product name
- Convert images with older/larger formats to .webp
- Upload the .webp images to an S3 bucket in product subfolders and each with a product name metadata tag 

## Instructions
1. Export WooCommerce CSV:
- The value for wc_csv is the path to a file that you export from WooCommerce. Under Products -> Export, check "ID", "Name", "Published", and "Images", then click "Generate CSV", and this file will download.
2. Fill in the appropriate values in the .env.example, then rename it to .env
- Examples/descriptions for required config values are in the .env.example file

3. Install Python and pip if not already installed

4. Run 
```
pip install pandas boto3 Pillow requests python-dotenv
```
then run 

```
python migrate-photos.py
```

