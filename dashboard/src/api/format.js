export const fmt = value => value == null ? '—' : typeof value === 'number' ? new Intl.NumberFormat(undefined,{maximumFractionDigits:2}).format(value) : String(value);
export const date = value => value ? new Date(value).toLocaleString() : 'Not exposed';
