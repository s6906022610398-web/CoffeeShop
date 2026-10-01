COFFEE SHOP MANAGEMENT SYSTEM
=============================

Python 3.10+
Standard Library only

PROJECT STRUCTURE
-----------------
CoffeeShop/
    main.py
    config.py
    database.py
    product.py
    order.py
    payment.py
    report.py
    README.txt
    data/
        products.dat
        orders.dat
        payments.dat
    report.txt   <-- generated after choosing menu 5

HOW TO RUN
----------
1. Open a terminal in the CoffeeShop folder.
2. Run:

   python main.py

MAIN MENU
---------
1. Add
2. Update
3. Delete
4. View
5. Generate Report
0. Exit

RECORD FORMAT
-------------
Endianness: Little-Endian (<)
String encoding: UTF-8
All records are fixed-length.

products.dat
    Struct: <i40s20sfiQ
    Size  : 80 bytes

orders.dat
    Struct: <iiif20siQ
    Size  : 48 bytes

payments.dat
    Struct: <ii20sf20siQ
    Size  : 68 bytes

IMPORTANT
---------
- quantity is an integer because a coffee quantity is a whole number.
- price, total and payment amount use Float (struct 'f'), 4 bytes.
- Payment methods are Cash and PromptPay.
- Delete uses a logical delete + free-list so deleted slots can be reused.
- IDs start at 2001 (products), 3001 (orders), and 4001 (payments)
  for a clean sample/report format.
- Order total is calculated automatically from product price x quantity.
- Payment amount is taken from the related order total.
- A product cannot be deleted while an active order references it.
- An order cannot be deleted while an active payment references it.

REPORT
------
Choose menu 5 to create/update report.txt.
The report includes:
- Products
- Orders
- Payments
- Database summary
- Payment summary
- Recent activity from the current program session

If a .dat file is intentionally corrupted, the program will stop with
a data-file error instead of silently using invalid data.
