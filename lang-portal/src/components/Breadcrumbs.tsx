import { Link, useLocation } from "react-router-dom"

export default function Breadcrumbs() {
  const location = useLocation()
  const pathnames = location.pathname.split('/').filter((x) => x)

  return (
    <nav className="mb-4 text-sm">
      <ol className="flex space-x-2">
        {pathnames.map((value, index) => {
          const path = `/${pathnames.slice(0, index + 1).join('/')}`
          const isLast = index === pathnames.length - 1
          
          return (
            <li key={path} className="flex items-center">
              {!isLast ? (
                <Link
                  to={path}
                  className="text-gray-500 hover:text-gray-700"
                >
                  {value.replace(/-/g, ' ')}
                </Link>
              ) : (
                <span className="text-gray-700 font-medium">
                  {value.replace(/-/g, ' ')}
                </span>
              )}
              {!isLast && <span className="mx-2">/</span>}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}