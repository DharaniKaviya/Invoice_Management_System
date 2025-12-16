export enum InvoiceStatus {
  DRAFT = 'Draft',
  PENDING = 'Pending',
  PAID = 'Paid',
  OVERDUE = 'Overdue'
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  address: string;
  phone?: string;
}

export interface Product {
  id: string;
  name: string;
  unitPrice: number;
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxRate: number; // percentage, e.g., 10 for 10%
}

export interface Invoice {
  id: string;
  number: string; // Readable invoice number e.g., INV-001
  customerId: string;
  customerName: string; // Denormalized for easier display
  customerAddress: string;
  date: string;
  dueDate: string;
  items: InvoiceItem[];
  subtotal: number;
  taxTotal: number;
  grandTotal: number;
  status: InvoiceStatus;
  notes?: string;
}

export interface InvoiceSummary {
  subtotal: number;
  taxTotal: number;
  grandTotal: number;
}