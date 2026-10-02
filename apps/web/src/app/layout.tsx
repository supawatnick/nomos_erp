import type { ReactNode } from 'react';
export const metadata = { title: 'NOMOS ERP', description: 'Inventory-first ERP' };
export default function RootLayout({ children }: { children: ReactNode }) { return <html lang="th"><body>{children}</body></html>; }
