import { NavLink, Route, Routes } from 'react-router-dom'
import { CountiesList } from './routes/CountiesList'
import { CountyDetail } from './routes/CountyDetail'
import { Placeholder } from './routes/Placeholder'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'font-semibold underline' : 'text-blue-600'

function App() {
  return (
    <div>
      <nav className="p-4 border-b flex gap-4">
        <NavLink to="/counties" className={navLinkClass}>
          County Boards
        </NavLink>
        <NavLink to="/turnout" className={navLinkClass}>
          Turnout
        </NavLink>
        <NavLink to="/demographics" className={navLinkClass}>
          Demographics
        </NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<CountiesList />} />
        <Route path="/counties" element={<CountiesList />} />
        <Route path="/counties/:slug" element={<CountyDetail />} />
        <Route path="/turnout" element={<Placeholder title="Turnout Rates" />} />
        <Route path="/demographics" element={<Placeholder title="Registered Voter Demographics" />} />
      </Routes>
    </div>
  )
}

export default App
