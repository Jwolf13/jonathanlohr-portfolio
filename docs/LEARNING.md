# Learning plan — style, layout, and the TypeScript that supports it

You said you want to personalize the site visually and feel confident editing the code. Honest truth: 80% of "making a site look better" is **Tailwind fluency + design taste**, not TypeScript. TypeScript is the safety net once you want to build new things confidently — it's not the paintbrush.

This doc is opinionated and ranked. Work top to bottom.

**How to use the search queries below**: paste them into Google or YouTube exactly as written. They're chosen because they reliably turn up canonical, high-quality results. I'm using search queries instead of direct URLs because URLs to specific videos, articles, and tweets rot fast — a search will still land you in the right place a year from now.

---

## 0. How to approach learning this without breaking your site

This section is about the *process* — how to learn safely, what to revisit, and how to understand the file structure so changes don't cascade in ways you didn't expect. Read this first. The numbered sections below are the *what*; this section is the *how*.

### The 5-step loop for every session

1. **Pick one small thing.** "Change the button color." "Add a card." "Make the hero text bigger." Not "redesign the homepage."
2. **Read the file you're about to touch end-to-end first.** Even if it looks intimidating. Reading is free; you don't have to understand every line on the first pass.
3. **Make the change.** Save.
4. **Verify locally** at `http://localhost:3000`. Works? Great. Doesn't? Ctrl+Z and try a different approach. You're allowed to fail — nothing is shipped yet.
5. **Commit and push.** Even tiny changes. `git commit -m "tweak: hero copy"` is enough. Every commit is a save point you can roll back to.

Step 5 is the safety net. **As long as you commit before trying something risky, nothing you do is permanent.** `git reset --hard HEAD` puts you back to the last commit.

### Blast radius — which files are scary, which are safe

Think of files in three tiers. Edit confidently at the bottom, carefully in the middle, deliberately at the top.

**Top tier — touch deliberately (one change at a time, test thoroughly)**
- `app/layout.tsx` — wraps every page. A bug here breaks every URL.
- `app/globals.css` — affects every element on the site.
- `package.json`, `next.config.ts`, `tsconfig.json` — toolchain. Don't change unless you're following a recipe.
- `.github/workflows/*.yml` — CI/CD. Breaking these means broken deploys.

**Middle tier — touch with care (changes ripple across multiple pages)**
- `components/SiteNav.tsx` — used in the layout, so on every page.
- `components/ProjectCard.tsx` — used on the homepage and `/projects`.
- `components/CaseStudyLayout.tsx` — used by every case study.
- Any file inside `components/` — by definition multiple places import them.

**Bottom tier — edit freely (low blast radius)**
- `app/<some-route>/page.tsx` — affects only that one URL.
- `content/projects.ts` and `content/sales-tools.ts` — pure data. Hard to break visually; TypeScript catches schema mistakes.
- `content/case-studies/*.tsx` — affects only one case-study page.

**Rule of thumb:** the deeper a file is in the dependency graph, the more careful you should be. A component imported by 10 pages affects 10 pages.

### Ho4at you're affecting

```
content/projects.ts          <-  data only, no UI. Safe to edit.
        |  (read by)
        v
app/projects/page.tsx        <-  one route. Affects /projects only.
        |  (renders)
        v
components/ProjectCard.tsx   <-  one card's UI. Affects everywhere it's used.
        |  (rendered inside)
        v
app/layout.tsx               <-  wraps every page. Affects everything.
        |  (styled by)
        v
app/globals.css              <-  base styles. Affects every element.
```

When you change something low in the chain (the data), one route updates. When you change something high (`layout.tsx`), every route updates. Always ask: *how far up the chain am I editing?*

The full picture is in `docs/architecture.drawio` and `docs/ARCHITECTURE.md`. Keep those open as references — they answer 90% of "where does this live?" questions.

### What to circle back to — revisit until it's muscle memory

You don't learn this stack once. You revisit the same handful of things until they're automatic:

- **Tailwind core-concepts docs** — the first 4 pages. Re-read every few weeks for the first 2 months. Each pass you understand more.
- **`content/projects.ts`** — every time you add a project. The shape of that file *is* the lesson on TypeScript types.
- **`components/ProjectCard.tsx`** — every time you want cards to look different. After 5 visits you'll know it cold.
- **`app/layout.tsx`** — every time you change anything global. Read it before touching it.
- **The Next.js docs page for whichever feature you're using** (`generateStaticParams`, `metadata`, `<Image>`). One feature at a time, as you need them — not all at once.

### A safe session looks like this

```bash
# 1. Pull latest and branch off main
git checkout main
git pull
git checkout -b experiment/bigger-hero-text

# 2. Start the dev server in one terminal
npm run dev

# 3. Edit one file. Save. Watch the browser reload at localhost:3000.

# 4. When happy, commit
git add -A
git commit -m "experiment: bigger hero text"

# 5. Push and open a PR
git push -u origin experiment/bigger-hero-text
# Open the PR URL GitHub prints

# 6. If CI passes and it looks right, merge to main.
#    The deploy workflow ships it to S3 + CloudFront automatically.
```

**Four escape hatches** worth memorizing — they mean you can never permanently break anything:

| Situation | Fix |
| --- | --- |
| Editor mistake, haven't committed yet | `Ctrl+Z`, or `git checkout -- <file>` to discard edits |
| Bad commit, want to undo but keep changes | `git reset --soft HEAD~1` |
| Bad commit, want to wipe everything | `git reset --hard HEAD~1` |
| Bad commit already pushed to main | `git revert <commit-sha>` creates a clean undo commit |

Knowing these four is worth more than knowing 100 Tailwind classes.

### Read the codebase in this order to make sense of it

If you've never sat down and traced how the site actually works, do this once. It takes 30 minutes and the whole mental model clicks.

1. Open `app/layout.tsx`. This is the shell of every page.
2. Open `app/page.tsx`. This is your homepage. It uses nothing fancy — just JSX.
3. Open `content/projects.ts`. This is a typed array. Notice the `Project` type at the top.
4. Open `app/projects/page.tsx`. See how it imports `projects` from the registry and renders them.
5. Open `components/ProjectCard.tsx`. See how it takes a `Project` prop and renders one card.
6. Open `app/projects/[slug]/page.tsx`. The `[slug]` folder name is what makes it dynamic. `generateStaticParams()` tells Next.js which slugs to pre-render.
7. Open `content/case-studies/channel-stream.tsx`. This is the content rendered inside that dynamic route.

By the end you've seen: data → page → component → dynamic route → content. That's the whole system.

### First 10 sessions, in order

The point of each is to touch one thing, see it work, gain confidence. Resist the urge to skip ahead.

1. Change one color on the home page (a button hover) and ship it.
2. Edit your headline copy and ship it.
3. Add a new tech tag to one project in `content/projects.ts`.
4. Replace an emoji icon with a Lucide icon (`npm install lucide-react`, import, render `<Zap />`).
5. Add a new section to your `/about` page (one paragraph and a heading).
6. Adjust spacing on the hero — try `py-24` → `py-32`, see what changes.
7. Add a new entry to `content/sales-tools.ts` for a tool you're planning to build.
8. Add a new top-level nav item (edit `components/SiteNav.tsx`, create the matching `app/<route>/page.tsx`).
9. Add a hover animation to project cards (`transition-transform hover:-translate-y-1`).
10. Write your first real case study for a project that's currently a stub.

By session 10 you'll know where everything lives and how to find what you need. The numbered sections below are about going deeper — but the doing is what makes it stick.

---

## 1. The single biggest unlock: Tailwind fluency

Your whole site is styled with Tailwind v4. Every visual change goes through Tailwind classes. A week here changes everything.

### Read these (canonical)

- **Tailwind docs** → [tailwindcss.com/docs](https://tailwindcss.com/docs)
  Start with the "Core Concepts" section in the left sidebar — read all 4 pages. About 90 minutes total. Keep the docs open while you work; the in-page search is fast.

- **Tailwind Play** → [play.tailwindcss.com](https://play.tailwindcss.com)
  Free in-browser sandbox with autocomplete. When you see a class you don't recognize, paste a snippet here and tweak it. This is where fluency actually builds.

- **VS Code extension: "Tailwind CSS IntelliSense"**
  Search the VS Code extension marketplace for that exact name. It autocompletes classes, shows the underlying CSS on hover, warns on typos. Install before anything else.

### Watch (search YouTube)

- **Search YouTube: `Adam Wathan utility first CSS`**
  Adam created Tailwind. There are several talks of his on this topic — any of them will do. He explains the *philosophy*, which is what makes the class names stop feeling random.

- **Search YouTube: `Lee Robinson Tailwind`**
  Lee runs DX at Vercel. He has multiple short videos building real components with Tailwind. Pick the most recent.

### The book that changes your eye

- **Refactoring UI** → [refactoringui.com](https://www.refactoringui.com) (~$99, by Adam Wathan + Steve Schoger)
  The single most useful design book for non-designers. Short chapters, before/after screenshots, every tip is actionable. The "Working with color" and "Hierarchy is everything" chapters alone will upgrade your portfolio.
- **Free alternative**: search Google for `Steve Schoger 7 practical tips for cheating at design`. There's a well-known free article that distills several of the book's ideas.

---

## 2. Layout patterns — getting boxes to behave

Tailwind is the vocabulary; layout is the grammar.

- **Josh Comeau's blog** → [joshwcomeau.com](https://www.joshwcomeau.com)
  Click "Articles" in the nav. Read in this order: "An Interactive Guide to Flexbox," "An Interactive Guide to CSS Grid," "Designing Beautiful Shadows in CSS." All free, all excellent.

- **CSS for JS Devs** → [css-for-js.dev](https://css-for-js.dev) (~$300, Josh Comeau's course)
  If you only buy one paid thing on this list, buy this. Modules 1–3 (Flexbox, Grid, Positioning) are exactly what you need. Free preview lessons are themselves a useful tutorial.

- **Every Layout** → [every-layout.dev](https://every-layout.dev)
  A pattern library of robust layout primitives (Stack, Cluster, Sidebar, Switcher). Changes how you *think* about layout — you stop fighting CSS and start composing it.

---

## 3. Design taste — sites worth stealing from

Fastest way to build taste: study good work, then ask "why does that feel different from mine?"

Open each in a tab, then open DevTools (right-click → Inspect):

- [linear.app](https://linear.app) — restraint, micro-interactions, type hierarchy
- [vercel.com](https://vercel.com) — gradient + dark mode done right
- [stripe.com](https://stripe.com) — the gold standard of dense-but-clear product marketing
- [leerob.io](https://leerob.io) — same stack as yours (Next.js + Tailwind). View source. Steal patterns.
- [brittanychiang.com](https://brittanychiang.com) — the canonical dev portfolio
- [maggieappleton.com](https://maggieappleton.com) — voice + visuals integrated; idiosyncratic, inspiring
- [nomadlist.com](https://nomadlist.com) — opinionated, dense; proof that "personal" beats "polished"

For each, ask: What's the type scale? How big is the body text? How much whitespace surrounds headings? What's the hover state on a card? Inspect — every site teaches for free.

---

## 4. TypeScript with React — the safety net

You don't need to "learn TypeScript" as a separate skill. You need to learn the patterns that show up in React: typing props, typing data, typing events. Small surface area.

- **Total TypeScript** → [totaltypescript.com](https://www.totaltypescript.com)
  Look in the nav for "Tutorials." Matt Pocock has a free "Beginners TypeScript" tutorial and a free "React with TypeScript" tutorial. Do them in that order. Each is interactive and takes a few hours.

- **Search Google: `react typescript cheatsheet`**
  The community React+TS cheatsheet is the canonical reference. Bookmark it, return when you need a recipe.

- **Search YouTube: `Matt Pocock TypeScript`**
  Matt's channel has dozens of short, focused tips. After the tutorials, his bite-size videos keep you sharp.

### What "good React+TS" already looks like in your code

Open `content/projects.ts` and `components/ProjectCard.tsx`. The pattern there is:

1. Define a `type` (`Project`) for your data shape.
2. Export an array typed with that type — the editor catches typos as you type.
3. Components accept that type as a prop. Renaming a field in one place breaks the editor everywhere it's used — you can't ship a half-renamed change.

That pattern is 70% of useful React+TS. Master it and you're set.

---

## 5. Next.js depth

You use a lot of Next.js features. Understanding them unlocks ones you don't know exist yet.

- **Next.js Learn** → [nextjs.org/learn](https://nextjs.org/learn)
  Free, official, interactive. Build a small app from scratch. ~4 hours. The "From JavaScript to React" and "Dashboard App" paths cover what your site already uses.

- **Next.js App Router docs** → [nextjs.org/docs/app](https://nextjs.org/docs/app)
  Reference, not a tutorial. The "Routing" and "Data Fetching" sections are the most-used.

- **Search YouTube: `Lee Robinson Next.js`**
  Short videos on specific features. He works at Vercel; his material stays current.

- **The docs that ship in your node_modules**
  Seriously. Run `ls node_modules/next/dist/docs/01-app/` and read whichever file matches what you're doing. For Next 16 these are often more up-to-date than the website.

---

## 6. Tools that accelerate the most

- **v0.dev** → [v0.dev](https://v0.dev)
  Vercel's UI generator. Describe a component ("pricing table with three tiers, blue accent, dark mode") and it returns working Tailwind + React. Copy into your repo and adjust. The fastest way to get good-looking starter components.

- **shadcn/ui** → [ui.shadcn.com](https://ui.shadcn.com)
  Copy-paste React components built on Tailwind + Radix. Beautiful defaults, full type safety, you own the code. For any "I don't want to build this from scratch" component (dialog, dropdown, command menu, tabs), start here.

- **Tailwind UI** → search Google for `Tailwind UI` (~$299, by the Tailwind team)
  Premium pre-built marketing and app layouts. Not free, but if you'll use this portfolio for years, it saves a hundred hours.

- **Aceternity UI** → [ui.aceternity.com](https://ui.aceternity.com)
  Flashy animation-heavy components. Steal one effect, not the whole vibe.

- **Lucide icons** → [lucide.dev](https://lucide.dev)
  Beautiful, consistent icons. Drop-in replacement for the emoji icons on your home page (`<Zap />`, `<Wrench />`).

### VS Code extensions worth installing now

Search each in the VS Code marketplace:

- `Tailwind CSS IntelliSense` (Tailwind autocomplete)
- `Pretty TypeScript Errors` (makes TS errors readable)
- `Error Lens` (inline error/warning display)
- `GitLens` (git history at a glance)
- `ES7+ React/Redux/React-Native snippets` (`rafce` → React component boilerplate)

---

## 7. A 4-week curriculum — actually realistic

30 minutes a day, top to bottom.

**Week 1 — Tailwind**
- Days 1–2: Tailwind docs core concepts pages
- Day 3: Watch an Adam Wathan talk (search YouTube: `Adam Wathan utility first CSS`)
- Days 4–5: Restyle one section of your site (suggestion: the hero). No new content — just play with classes and watch what changes. Use Tailwind Play for fast iteration.
- Weekend: Read three chapters of Refactoring UI, or skim Josh Comeau's free Flexbox + Grid articles.

**Week 2 — Layout & design eye**
- Days 1–3: Josh Comeau's free Flexbox + Grid interactive guides
- Days 4–5: Open Linear, Vercel, Lee Robinson's site. Inspect-element. Recreate one element you like in Tailwind Play.
- Weekend: Pick one section of your site (homepage cards, or project cards). Rebuild it pixel-by-pixel from a reference site you admire.

**Week 3 — TypeScript with React**
- Days 1–3: Matt Pocock's free Beginners TypeScript tutorial (totaltypescript.com → Tutorials)
- Days 4–5: Matt Pocock's free React with TypeScript tutorial
- Weekend: Refactor one component to use stricter types. Add a new field to the `Project` type and let TypeScript guide you through the changes.

**Week 4 — Compose & ship**
- Days 1–2: Browse shadcn/ui. Install one component (suggested: `<Tabs>` for the projects page).
- Day 3: Try v0.dev — describe a component you want, copy the result in.
- Days 4–5: Add something to the site you couldn't have built four weeks ago. Pricing cards on Sales Tools? Theme toggle? Grid of skill badges?
- Weekend: Push to main. Write one paragraph in the commit message about what you changed. That paragraph is your first dev-blog entry, even before you have a blog page.

---

## 8. Five quick wins you could ship this week

1. **Theme toggle.** Your site already supports dark mode via Tailwind's `dark:` variants — you just need a button that toggles the `dark` class on `<html>`. Search Google: `shadcn theme toggle next.js` for the canonical recipe.

2. **Replace emoji icons (⚡, 🛠) with Lucide icons.** `npm install lucide-react`. `<Zap />` and `<Wrench />` look more polished than emoji and respond to color classes.

3. **Type-scale rhythm.** Right now your h1/h2/body sizes are ad-hoc. Pick a scale (e.g., `text-5xl / text-3xl / text-xl / text-base / text-sm`) and use it consistently. Refactoring UI has a whole chapter on this.

4. **Animate project cards on hover.** Add `transition-transform hover:-translate-y-1` to `components/ProjectCard.tsx`. Tiny change, feels much more alive.

5. **Open-graph metadata for social previews.** When someone posts your URL in Slack/LinkedIn, it's plain text right now. Search Google: `Next.js opengraph-image metadata` — Next.js has a built-in way to add `opengraph-image.png` and the `metadata` export. 30 minutes, permanent professional polish.

---

## 9. When you're stuck

- **Tailwind docs search bar.** Faster than Google for class lookups.
- **Search Stack Overflow with the literal error message.** Almost always already answered.
- **Ask Claude in a fresh chat with the exact file path, the exact snippet, and what you're trying to do.** Don't paraphrase the error — paste it.
- **Search GitHub** for `tailwindcss next.js portfolio` (or similar) and read open-source examples. Other people's code is the cheapest learning available.

---

## 10. What I'd skip (or save for later)

- **Generic "Learn JavaScript in 2024" courses.** You can already build the site — you don't need fundamentals from scratch.
- **CSS-in-JS libraries (styled-components, Emotion, vanilla-extract).** Tailwind covers this; adding another styling system is a step backwards.
- **Animation libraries (framer-motion).** Tailwind transitions are enough until you have a specific need.
- **MDX.** Your case studies are TSX components and that's fine. Move to MDX only when you have a real blog with 10+ posts.
- **A CMS (Sanity, Contentful, etc.).** You'd be re-decentralizing your own files. The TypeScript registries are already your CMS.

---

## Honest meta-advice

You'll go further by **shipping a small change a day** than reading a book a week. Open `app/page.tsx`, change a color, save, see it at `localhost:3000`. Do that 30 times and Tailwind starts to feel native. The compounding kicks in fast.
