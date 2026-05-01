import type { Metadata } from "next"
import "./globals.css"
import { AuthProvider } from "@/components/AuthContext"
import { Sidebar } from "@/components/Sidebar"
import { TopBar } from "@/components/TopBar"

export const metadata: Metadata = {
  title: "Channel Stream",
  description: "Your unified streaming guide",
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white min-h-screen">
        <AuthProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
              <TopBar />
              <main className="flex-1 p-8">
                {children}
              </main>
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  )
}
