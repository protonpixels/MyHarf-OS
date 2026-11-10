const usdFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

/** Format an integer amount in cents for display; financial calculations stay on the backend. */
export function formatCurrency(cents: number, currency = 'USD', locale = 'en-US'): string {
  if (!Number.isSafeInteger(cents)) throw new TypeError('Currency amounts must be safe integer cents.')
  const formatter = currency === 'USD' && locale === 'en-US'
    ? usdFormatter
    : new Intl.NumberFormat(locale, { style: 'currency', currency })
  return formatter.format(cents / 100)
}
