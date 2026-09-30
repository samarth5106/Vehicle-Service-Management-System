import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'RevUp | Vehicle Service Management System',
  description: 'Manage customers, vehicles, service jobs, parts and invoices for an automobile service center.',
  icons: { icon: '/icon.svg' },
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>
}
