
Flask / Django  Exam

- Create new application with flask and django



*Models:

     *** Notes:
           --add this fields for all models (created_at , created_by , updated_at , updated_by) 
            --can you add any fields to implement business logic


  - Users (master) (id , name, email, password, status, role_id)
  - Roles  (master) (id, name, parent_role_id ,status)
        - Permissions(detail)  (id, role_id, create, read, update, delete, model_name)
  - Customers (master)  (id, name, email, address, phone, mobile)
  - Products (master)  (id, name, price, quantity, description)
  - Invoices (master)  (id , customer_id, invoice_date, total_amount, status[pending ,paid, refused] )
        - InvoiceProducts (detail)  (id, product_id, quantity, amount)



*Roles 





                                                      Permissions for admin 
model	create	read	update	delete	role
Users	1	1	1	1	Admin 
Roles	1	1	1	1	Admin 
Permissions	1	1	1	1	Admin 
Customers	1	1	1	1	Admin 
Products	1	1	1	1	Admin
Invoices	1	1	1	1	Admin
InvoiceProducts	1	1	1	1	Admin
- full permissions 
- parent_role_id = null

                                                    Permissions for all Sales managers 
model	create	read	update	delete	role
Users	1	1	1	0	Sales managers  1-2 
Roles	1	1	1	0	Sales managers  1-2 
Permissions	1	1	1	0	Sales managers  1-2 
Customers	1	1	1	0	Sales managers  1-2 
Products	1	1	1	0	Sales managers  1-2
Invoices	1	1	1	0	Sales managers  1-2
InvoiceProducts	1	1	1	0	Sales managers  1-2
-  parent_role_id = admin role id
-  Sales manager 1 cannot read or create or update  Sales manager2
-  can (read-create-update)  for assgined role  and childs roles
-  when create new role  the parent_role_id inserted from backend not from request
-  can change invoice status from pending to paid or refused

                                                    Permissions for all Sales employees 
model	create	read	update	delete	role
Users	1	1	0	0	Sales employees  1-2 
Roles	1	1	0	0	Sales employees  1-2 
Permissions	1	1	0	0	Sales employees  1-2 
Customers	1	1	0	0	Sales employees  1-2 
Products	1	1	0	0	Sales employees  1-2
Invoices	1	1	0	0	Sales employees  1-2
InvoiceProducts	1	1	0	0	Sales employees  1-2
-  parent_role_id = sales manager role id
-  Sales employee 1 cannot read or create or update  Sales  employee 2
-  can (read-create)  for assgined role  or childs roles
-  when create new role  the parent_role_id inserted from backend not from request
-  can create new invoice and the default status pending


                                                    Permissions for all Cashiers 
model	create	read	update	delete	role
Products	0	1	0	0	All cashiers
Invoices	1	1	0	0	All cashiers
InvoiceProducts	1	1	0	0	All cashiers
-  parent_role_id = sales employee role id
-  cashier  cannot read or create or update  other cashier
-  can (read-create)  for assgined role  
-  can create new invoice and the default status pending







*Validations:
- create new class for validations layer before (CRUD) for  check
            (data types - min&max length- unique – required – data format(email – password - …..)) 
    ***note- don’t use ORM validations


*Authentication:
- use JWT token






 










