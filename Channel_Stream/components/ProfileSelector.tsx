"use client"

import { useState } from "react"
import { Profile } from "@/lib/store"

type Props = {
  profiles: Profile[]
  activeProfileId: string
  onSwitch: (id: string) => void
  onAdd: (name: string) => void
  onRemove: (id: string) => void
}

export function ProfileSelector({
  profiles,
  activeProfileId,
  onSwitch,
  onAdd,
  onRemove,
}: Props) {
  const [open, setOpen] = useState(false)
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState("")

  const active = profiles.find((p) => p.id === activeProfileId)

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    const name = newName.trim()
    if (!name) return
    onAdd(name)
    setNewName("")
    setAdding(false)
    setOpen(false)
  }

  function close() {
    setOpen(false)
    setAdding(false)
    setNewName("")
  }

  return (
    <div className="relative" data-testid="profile-selector">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 transition-colors border border-zinc-700"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Switch profile"
      >
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0 select-none"
          style={{ backgroundColor: active?.color ?? "#525252" }}
          aria-hidden="true"
        >
          {active?.name.slice(0, 1).toUpperCase() ?? "?"}
        </div>
        <span className="text-sm font-medium text-zinc-200 max-w-[100px] truncate">
          {active?.name ?? "Profile"}
        </span>
        <svg
          className={`w-4 h-4 text-zinc-400 transition-transform duration-150 ${open ? "rotate-180" : ""}`}
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={close}
            aria-hidden="true"
          />
          <div
            className="absolute right-0 top-full mt-2 z-20 w-64 bg-zinc-900 border border-zinc-700 rounded-2xl shadow-2xl overflow-hidden"
            role="listbox"
            aria-label="Profiles"
          >
            <div className="p-2">
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-3 py-2">
                Profiles ({profiles.length}/6)
              </p>

              {profiles.map((profile) => {
                const isActive = profile.id === activeProfileId
                return (
                  <div
                    key={profile.id}
                    role="option"
                    aria-selected={isActive}
                    data-testid={`profile-option-${profile.id}`}
                    className={[
                      "flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer group",
                      isActive ? "bg-zinc-800" : "hover:bg-zinc-800/60",
                    ].join(" ")}
                    onClick={() => {
                      onSwitch(profile.id)
                      close()
                    }}
                  >
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 select-none"
                      style={{ backgroundColor: profile.color }}
                      aria-hidden="true"
                    >
                      {profile.name.slice(0, 1).toUpperCase()}
                    </div>
                    <span className="flex-1 text-sm font-medium text-zinc-200 truncate">
                      {profile.name}
                    </span>
                    {isActive ? (
                      <svg
                        className="w-4 h-4 text-emerald-400 flex-shrink-0"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-label="Active"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      !profile.isDefault && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onRemove(profile.id)
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                          aria-label={`Remove ${profile.name}`}
                          data-testid={`remove-profile-${profile.id}`}
                        >
                          <svg
                            className="w-3.5 h-3.5"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </button>
                      )
                    )}
                  </div>
                )
              })}
            </div>

            {profiles.length < 6 && (
              <div className="border-t border-zinc-800 p-2">
                {adding ? (
                  <form onSubmit={handleAdd} className="flex gap-2 px-1">
                    <input
                      autoFocus
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="Profile name"
                      maxLength={20}
                      className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      data-testid="new-profile-name-input"
                    />
                    <button
                      type="submit"
                      className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
                      data-testid="confirm-add-profile"
                    >
                      Add
                    </button>
                  </form>
                ) : (
                  <button
                    onClick={() => setAdding(true)}
                    className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 transition-colors text-sm"
                    data-testid="add-profile-button"
                  >
                    <svg
                      className="w-4 h-4"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Add profile
                  </button>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
