import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <header className="mb-8 w-full">
          <h1 className="text-3xl font-semibold text-black dark:text-zinc-50">
            Jonathan Lohr – Cloud Architect
          </h1>
          <nav className="mt-4">
            <ul className="flex gap-4 text-blue-600">
              <li>
                <Link href="/projects">Projects</Link>
              </li>
              <li>
                <Link href="/architecture-cases">Architecture Cases</Link>
              </li>
              <li>
                <Link href="/consulting">Consulting</Link>
              </li>
            </ul>
          </nav>
        </header>

        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={100}
          height={20}
          priority
        />

        {/* the rest of the starter content */}
        {/* ... you can keep or delete pieces as you like */}
      </main>
    </div>
  );
}