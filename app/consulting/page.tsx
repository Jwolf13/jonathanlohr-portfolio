"use client";

import { useState } from "react";

export default function ConsultingPage() {
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    "idle"
  );
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("loading");
    setError(null);

    const form = e.currentTarget;
    const formData = new FormData(form);

    const body = {
      name: formData.get("name"),
      email: formData.get("email"),
      message: formData.get("message"),
    };

    try {
      // 1) Save to DynamoDB via existing Lambda
      const saveRes = await fetch(
        "https://1n76g8v617.execute-api.us-east-1.amazonaws.com/contact",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!saveRes.ok) {
        throw new Error("Save failed");
      }

      // 2) Send confirmation email via SES Lambda
      const emailRes = await fetch(
        "https://1n76g8v617.execute-api.us-east-1.amazonaws.com/consulting-contact",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!emailRes.ok) {
        throw new Error("Email failed");
      }

      setStatus("success");
      form.reset();
    } catch (err) {
      console.error(err);
      setStatus("error");
      setError("Something went wrong. Please try again.");
    }
  }

  return (
    <main className="max-w-xl mx-auto py-12">
      <h1 className="text-3xl font-semibold mb-6">Consulting</h1>
      <p className="mb-6">
        Tell me a bit about your project and how I&apos;ll help. I&apos;ll get
        back to you by email.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1" htmlFor="name">
            Name
          </label>
          <input
            id="name"
            name="name"
            type="text"
            required
            className="w-full border px-3 py-2 rounded"
          />
        </div>

        <div>
          <label className="block mb-1" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            className="w-full border px-3 py-2 rounded"
          />
        </div>

        <div>
          <label className="block mb-1" htmlFor="message">
            Message
          </label>
          <textarea
            id="message"
            name="message"
            required
            rows={5}
            className="w-full border px-3 py-2 rounded"
          />
        </div>

        <button
          type="submit"
          disabled={status === "loading"}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {status === "loading" ? "Sending..." : "Send message"}
        </button>

        {status === "success" && (
          <p className="text-green-600 mt-2">
            Thanks! Your message has been sent.
          </p>
        )}
        {status === "error" && (
          <p className="text-red-600 mt-2">{error}</p>
        )}
      </form>
    </main>
  );
}