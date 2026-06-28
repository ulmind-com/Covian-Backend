import pymongo

OLD_URI = "mongodb+srv://premjeetdev26_db_user:premjeet.dev26%4026@cluster0.gbuzumt.mongodb.net/project_form_prem"
NEW_URI = "mongodb+srv://covianweb_db_user:covian%40123@cluster0.okzrfu1.mongodb.net/project_form_prem"
DB_NAME = "project_form_prem"

def migrate():
    print("Connecting to old database...")
    old_client = pymongo.MongoClient(OLD_URI)
    old_db = old_client[DB_NAME]

    print("Connecting to new database...")
    new_client = pymongo.MongoClient(NEW_URI)
    new_db = new_client[DB_NAME]

    collections = old_db.list_collection_names()
    print(f"Found {len(collections)} collections to migrate: {collections}")

    for coll_name in collections:
        print(f"\nMigrating collection: {coll_name}...")
        old_coll = old_db[coll_name]
        new_coll = new_db[coll_name]

        # Fetch all documents
        docs = list(old_coll.find({}))
        if not docs:
            print(f"Collection {coll_name} is empty. Skipping.")
            continue
        
        # Clear new collection just in case
        new_coll.delete_many({})
        
        # Insert documents
        new_coll.insert_many(docs)
        print(f"Successfully inserted {len(docs)} documents into {coll_name}.")

    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()
