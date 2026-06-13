from executor import Database

def main():
    db = Database()
    print("MyDB - type SQL commands, 'exit' to quit")

    while True:
        try:
            sql = input("mydb> ").strip()
        except EOFError:
            break

        if sql.lower() in ('exit', 'quit'):
            break
        if not sql:
            continue

        try:
            result = db.execute(sql)
            if result is not None:
                print(result)
        except Exception as e:
            print(f"Error: {e}")

    db.close()
    print("Goodbye!")

if __name__ == "__main__":
    main()