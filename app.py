# app.py
from flask import Flask, jsonify, request, render_template, make_response
from flask_cors import CORS
from mysql.connector import Error
from datetime import datetime

from db import get_connection

app = Flask(__name__, static_folder="static", template_folder=".")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---------- ROOT (SERVE SPA) ----------

@app.route("/")
def index():
    return render_template("index.html")

# ---------- CLIENT APIs ----------

@app.route("/api/clients", methods=["GET"])
def get_clients():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name, email, address FROM clients ORDER BY name")
        clients = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "clients": clients}), 200
    except Error as e:
        print("GET /api/clients DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print("GET /api/clients server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

@app.route("/api/clients", methods=["POST"])
def add_client():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        print("POST /api/clients JSON error:", e, "raw:", request.data)
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip() or None
    address = (data.get("address") or "").strip() or None

    if len(name) < 2:
        return jsonify({"success": False, "message": "Client name must be at least 2 characters"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # case‑insensitive duplicate check
        cur.execute("SELECT id FROM clients WHERE LOWER(name) = LOWER(%s)", (name,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Client already exists"}), 409

        cur.execute(
            "INSERT INTO clients (name, email, address) VALUES (%s,%s,%s)",
            (name, email, address)
        )
        conn.commit()
        client_id = cur.lastrowid
        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Client added successfully",
            "client": {"id": client_id, "name": name, "email": email, "address": address}
        }), 201
    except Error as e:
        print("POST /api/clients DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print("POST /api/clients server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------- ITEM APIs ----------

@app.route("/api/items", methods=["GET"])
def get_items():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name, unit_price, gst_percent FROM items ORDER BY name")
        items = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "items": items}), 200
    except Error as e:
        print("GET /api/items DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print("GET /api/items server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

@app.route("/api/items", methods=["POST"])
def add_item():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        print("POST /api/items JSON error:", e, "raw:", request.data)
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    name = (data.get("name") or "").strip()
    try:
        unit_price = float(data.get("unit_price"))
        gst_percent = float(data.get("gst_percent"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid price or GST"}), 400

    if len(name) < 2:
        return jsonify({"success": False, "message": "Item name must be at least 2 characters"}), 400
    if unit_price < 0:
        return jsonify({"success": False, "message": "Price cannot be negative"}), 400
    if gst_percent < 0 or gst_percent > 100:
        return jsonify({"success": False, "message": "GST percent must be between 0 and 100"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT id FROM items WHERE LOWER(name) = LOWER(%s)", (name,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Item already exists"}), 409

        cur.execute(
            "INSERT INTO items (name, unit_price, gst_percent) VALUES (%s,%s,%s)",
            (name, unit_price, gst_percent)
        )
        conn.commit()
        item_id = cur.lastrowid
        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Item added successfully",
            "item": {"id": item_id, "name": name, "unit_price": unit_price, "gst_percent": gst_percent}
        }), 201
    except Error as e:
        print("POST /api/items DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print("POST /api/items server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------- INVOICE LIST ----------

@app.route("/api/invoices", methods=["GET"])
def list_invoices():
    """
    Returns all invoices with totals and client name.
    """
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT i.id, i.invoice_number, i.invoice_date, i.due_date,
                   i.status, i.subtotal, i.tax_total, i.grand_total,
                   c.name AS client_name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            ORDER BY i.id DESC
        """)
        invoices = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "invoices": invoices}), 200
    except Error as e:
        print("GET /api/invoices DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print("GET /api/invoices server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------- CREATE INVOICE ----------

@app.route("/api/invoices", methods=["POST"])
def create_invoice():
    """
    Body JSON:
    {
      "client_id": 1,
      "invoice_date": "2025-12-19",
      "due_date": "2025-12-25",
      "status": "Pending",
      "billing_address": "...",
      "notes": "...",
      "items": [
        {
          "item_id": 3,        # optional, for linking to catalog
          "name": "Custom Name",
          "quantity": 2,
          "unit_price": 500,
          "gst_percent": 18
        }
      ]
    }
    """
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        print("POST /api/invoices JSON error:", e, "raw:", request.data)
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    # client_id
    try:
        client_id = int(data.get("client_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid client id"}), 400

    items = data.get("items") or []
    if not items:
        return jsonify({"success": False, "message": "At least one line item is required"}), 400

    invoice_date = data.get("invoice_date")
    due_date = data.get("due_date")
    status = (data.get("status") or "Draft").strip()
    billing_address = (data.get("billing_address") or "").strip()
    notes = (data.get("notes") or "").strip() or None

    try:
        datetime.strptime(invoice_date, "%Y-%m-%d")
        datetime.strptime(due_date, "%Y-%m-%d")
    except Exception:
        return jsonify({"success": False, "message": "Dates must be in YYYY-MM-DD format"}), 400

    subtotal = 0.0
    tax_total = 0.0
    normalized_items = []

    for it in items:
        name = (it.get("name") or "").strip()
        if len(name) < 1:
            return jsonify({"success": False, "message": "Item name is required for all lines"}), 400
        try:
            quantity = float(it.get("quantity"))
            unit_price = float(it.get("unit_price"))
            gst_percent = float(it.get("gst_percent"))
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Invalid quantity/price/GST in items"}), 400
        if quantity <= 0 or unit_price < 0:
            return jsonify({"success": False, "message": "Quantity must be >0 and price >=0"}), 400
        if gst_percent < 0 or gst_percent > 100:
            return jsonify({"success": False, "message": "GST percent must be between 0 and 100"}), 400

        line_amount = quantity * unit_price
        line_tax = line_amount * gst_percent / 100.0
        subtotal += line_amount
        tax_total += line_tax

        normalized_items.append({
            "item_id": it.get("item_id"),
            "name": name,
            "quantity": quantity,
            "unit_price": unit_price,
            "gst_percent": gst_percent
        })

    grand_total = subtotal + tax_total

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # validate client exists
        cur.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Client not found"}), 400

        # insert invoice
        cur.execute("""
            INSERT INTO invoices
            (client_id, invoice_date, due_date, status,
             billing_address, notes, subtotal, tax_total, grand_total)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (client_id, invoice_date, due_date, status,
              billing_address, notes, subtotal, tax_total, grand_total))
        conn.commit()
        invoice_id = cur.lastrowid

        # generate invoice number
        invoice_number = f"INV-{invoice_id:05d}"
        cur.execute("UPDATE invoices SET invoice_number=%s WHERE id=%s",
                    (invoice_number, invoice_id))
        conn.commit()

        # insert items
        for ni in normalized_items:
            cur.execute("""
                INSERT INTO invoice_items
                (invoice_id, item_id, item_name, quantity, unit_price, gst_percent)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                invoice_id,
                ni["item_id"],
                ni["name"],
                ni["quantity"],
                ni["unit_price"],
                ni["gst_percent"]
            ))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Invoice created successfully",
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "grand_total": grand_total
        }), 201
    except Error as e:
        print("POST /api/invoices DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print("POST /api/invoices server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------- GET INVOICE DETAILS ----------

@app.route("/api/invoices/<int:invoice_id>", methods=["GET"])
def get_invoice_details(invoice_id):
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT i.*, c.name AS client_name, c.email AS client_email, c.address AS client_address
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE i.id = %s
        """, (invoice_id,))
        inv = cur.fetchone()
        if not inv:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Invoice not found"}), 404

        cur.execute("""
            SELECT id, item_id, item_name, quantity, unit_price, gst_percent
            FROM invoice_items
            WHERE invoice_id = %s
        """, (invoice_id,))
        items = cur.fetchall()

        inv["items"] = items

        cur.close()
        conn.close()
        return jsonify({"success": True, "invoice": inv}), 200
    except Error as e:
        print(f"GET /api/invoices/{invoice_id} DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print(f"GET /api/invoices/{invoice_id} server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------- DELETE INVOICE (optional but useful) ----------

@app.route("/api/invoices/<int:invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM invoice_items WHERE invoice_id = %s", (invoice_id,))
        cur.execute("DELETE FROM invoices WHERE id = %s", (invoice_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Invoice deleted"}), 200
    except Error as e:
        print(f"DELETE /api/invoices/{invoice_id} DB error:", e)
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    except Exception as e:
        print(f"DELETE /api/invoices/{invoice_id} server error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

if __name__ == "__main__":
    # Keep debug=True while you are still integrating.
    app.run(debug=True)
