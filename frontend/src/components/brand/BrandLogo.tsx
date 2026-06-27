import { Link } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'
import { ObollaMark } from './ObollaMark'

type BrandLogoProps = {
  variant?: 'header' | 'footer' | 'hero'
  linked?: boolean
}

export function BrandLogo({ variant = 'header', linked = true }: BrandLogoProps) {
  const { tr } = useLocale()
  const size = variant === 'hero' ? 'lg' : variant === 'footer' ? 'sm' : 'md'
  const showTagline = variant !== 'footer'

  const content = (
    <span className="group inline-flex items-center rounded-xl transition">
      <ObollaMark size={size} showTagline={showTagline} tagline={tr('brandTagline')} />
    </span>
  )

  if (!linked) return content

  return (
    <Link
      to="/"
      className="shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-market)] rounded-xl"
    >
      {content}
    </Link>
  )
}