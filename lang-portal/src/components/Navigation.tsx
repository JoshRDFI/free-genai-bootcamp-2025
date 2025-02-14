import { Link } from "react-router-dom"
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList } from "@/components/ui/navigation-menu"

export default function Navigation() {
  const links = [
    { path: "/dashboard", label: "Dashboard" },
    { path: "/study-activties", label: "Study Activities" },
    { path: "/word-groups", label: "Word Groups" },
    { path: "/words", label: "Words" },
    { path: "/sessions", label: "Sessions" },
    { path: "/settings", label: "Settings" },
  ]

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <NavigationMenu>
          <NavigationMenuList className="h-16">
            {links.map((link) => (
              <NavigationMenuItem key={link.path}>
                <NavigationMenuLink asChild>
                  <Link
                    to={link.path}
                    className="px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
        </NavigationMenu>
      </div>
    </nav>
  )
}