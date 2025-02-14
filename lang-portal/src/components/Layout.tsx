import { Outlet } from "react-router-dom"
import Navigation from "./Navigation"
import Breadcrumbs from "./Breadcrumbs"

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Breadcrumbs />
        <Outlet /> {/* Page content will render here */}
      </div>
    </div>
  )
}