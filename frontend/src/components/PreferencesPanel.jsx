import { useState } from 'react'

const EXPERIENCE_OPTIONS = ['entry', 'mid', 'senior']
const WORK_MODE_OPTIONS = ['remote', 'hybrid', 'on-site']
const WORK_TYPE_OPTIONS = ['full-time', 'part-time', 'contract', 'internship']

function TagInput({ tags, onChange, placeholder }) {
  const [input, setInput] = useState('')

  const add = () => {
    const val = input.trim().toLowerCase()
    if (val && !tags.includes(val)) onChange([...tags, val])
    setInput('')
  }

  const remove = (tag) => onChange(tags.filter((t) => t !== tag))

  const onKey = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      add()
    }
    if (e.key === 'Backspace' && !input && tags.length) {
      remove(tags[tags.length - 1])
    }
  }

  return (
    <div className="flex flex-wrap gap-1.5 p-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 min-h-[42px] cursor-text"
      onClick={() => document.getElementById(`tag-input-${placeholder}`)?.focus()}
    >
      {tags.map((t) => (
        <span key={t} className="flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 rounded-md text-xs font-medium">
          {t}
          <button onClick={() => remove(t)} className="hover:text-red-500 leading-none font-bold">×</button>
        </span>
      ))}
      <input
        id={`tag-input-${placeholder}`}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKey}
        onBlur={add}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="flex-1 min-w-[140px] bg-transparent text-sm focus:outline-none placeholder-gray-400"
      />
    </div>
  )
}

function CheckboxGroup({ options, selected, onChange, capitalize = true }) {
  const toggle = (val) =>
    onChange(selected.includes(val) ? selected.filter((v) => v !== val) : [...selected, val])

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <label key={opt} className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={selected.includes(opt)}
            onChange={() => toggle(opt)}
            className="w-3.5 h-3.5 rounded accent-blue-600"
          />
          <span className={`text-sm ${capitalize ? 'capitalize' : ''}`}>{opt}</span>
        </label>
      ))}
    </div>
  )
}

export default function PreferencesPanel({ preferences, onSave, isSaving }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(preferences)

  // Sync when parent prefs load
  if (JSON.stringify(form) !== JSON.stringify(preferences) && !open) {
    setForm(preferences)
  }

  const set = (key) => (val) => setForm((f) => ({ ...f, [key]: val }))

  const handleSave = () => onSave(form)

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
      {/* Header / toggle */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold">Search Preferences</span>
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {preferences.roles?.length ?? 0} role keyword(s)
            {preferences.work_mode?.length ? ` · ${preferences.work_mode.join(', ')}` : ''}
            {preferences.experience?.length ? ` · ${preferences.experience.join('/')}` : ''}
          </span>
        </div>
        <span className="text-gray-400 text-lg leading-none">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-gray-100 dark:border-gray-700 space-y-5 pt-4">

          {/* Roles */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Role Keywords <span className="text-red-500">*</span>
              <span className="ml-1 text-gray-400 font-normal text-xs">(press Enter or comma to add)</span>
            </label>
            <TagInput
              tags={form.roles ?? []}
              onChange={set('roles')}
              placeholder="e.g. react engineer, frontend developer…"
            />
          </div>

          {/* Locations */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Locations
              <span className="ml-1 text-gray-400 font-normal text-xs">(empty = any)</span>
            </label>
            <TagInput
              tags={form.locations ?? []}
              onChange={set('locations')}
              placeholder="e.g. remote, london, new york…"
            />
          </div>

          {/* Experience + Work Mode + Work Type in a grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Experience <span className="text-gray-400 font-normal text-xs">(empty = any)</span>
              </label>
              <CheckboxGroup
                options={EXPERIENCE_OPTIONS}
                selected={form.experience ?? []}
                onChange={set('experience')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Work Mode <span className="text-gray-400 font-normal text-xs">(empty = any)</span>
              </label>
              <CheckboxGroup
                options={WORK_MODE_OPTIONS}
                selected={form.work_mode ?? []}
                onChange={set('work_mode')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Work Type <span className="text-gray-400 font-normal text-xs">(empty = any)</span>
              </label>
              <CheckboxGroup
                options={WORK_TYPE_OPTIONS}
                selected={form.work_type ?? []}
                onChange={set('work_type')}
              />
            </div>
          </div>

          {/* Salary */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Salary Range (USD/yr)
              <span className="ml-1 text-gray-400 font-normal text-xs">
                (optional — applies when salary data is available)
              </span>
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Min e.g. 80000"
                value={form.salary_min ?? ''}
                onChange={(e) => set('salary_min')(e.target.value ? Number(e.target.value) : null)}
                className="w-40 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-gray-400">–</span>
              <input
                type="number"
                placeholder="Max e.g. 140000"
                value={form.salary_max ?? ''}
                onChange={(e) => set('salary_max')(e.target.value ? Number(e.target.value) : null)}
                className="w-40 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Save */}
          <div className="flex items-center gap-3 pt-1">
            <button
              onClick={handleSave}
              disabled={isSaving || !form.roles?.length}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg font-semibold text-sm transition-colors"
            >
              {isSaving ? 'Saving…' : 'Save Preferences'}
            </button>
            {!form.roles?.length && (
              <p className="text-xs text-red-500">Add at least one role keyword</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
