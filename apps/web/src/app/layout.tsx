import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "NOMOS ERP", description: "Inventory-first ERP" };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="th"><body>{children}</body></html>; }
