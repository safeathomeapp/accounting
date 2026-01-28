const inputClass = 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white'

function Label({ label, required }) {
  if (!label) return null
  return (
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
      {label}{required && <span className="text-red-500 ml-1">*</span>}
    </label>
  )
}

function ErrorMsg({ error }) {
  if (!error) return null
  return <p className="text-red-600 text-xs mt-1">{error}</p>
}

export function TextInput({ label, required, error, ...props }) {
  return (
    <div>
      <Label label={label} required={required} />
      <input type="text" className={inputClass} {...props} />
      <ErrorMsg error={error} />
    </div>
  )
}

export function SelectInput({ label, required, error, options = [], placeholder, ...props }) {
  return (
    <div>
      <Label label={label} required={required} />
      <select className={inputClass} {...props}>
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) =>
          typeof opt === 'string'
            ? <option key={opt} value={opt}>{opt}</option>
            : <option key={opt.value} value={opt.value}>{opt.label}</option>
        )}
      </select>
      <ErrorMsg error={error} />
    </div>
  )
}

export function NumberInput({ label, required, error, prefix, ...props }) {
  return (
    <div>
      <Label label={label} required={required} />
      <div className="relative">
        {prefix && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400 text-sm pointer-events-none">
            {prefix}
          </span>
        )}
        <input
          type="number"
          step="0.01"
          className={`${inputClass} ${prefix ? 'pl-7' : ''}`}
          {...props}
        />
      </div>
      <ErrorMsg error={error} />
    </div>
  )
}

export function DateInput({ label, required, error, ...props }) {
  return (
    <div>
      <Label label={label} required={required} />
      <input type="date" className={inputClass} {...props} />
      <ErrorMsg error={error} />
    </div>
  )
}

export function TextArea({ label, required, error, rows = 3, ...props }) {
  return (
    <div>
      <Label label={label} required={required} />
      <textarea rows={rows} className={`${inputClass} resize-none`} {...props} />
      <ErrorMsg error={error} />
    </div>
  )
}
