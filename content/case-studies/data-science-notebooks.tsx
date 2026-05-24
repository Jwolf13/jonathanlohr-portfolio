import { Section } from "@/components/CaseStudyLayout";

export default function DataScienceNotebooks() {
  return (
    <>
      <Section title="What this is">
        <p>
          A collection of Jupyter notebooks exploring probability problems
          end-to-end — setup, simulation, analytical solution, and
          visualization. Less &quot;production ML&quot;, more &quot;sharpen the
          intuition.&quot;
        </p>
      </Section>

      <Section title="Notebooks">
        <p>
          <strong>Golf shot probability.</strong> Models the distribution of
          tee-shot outcomes given a known dispersion pattern and course
          geometry. Useful as a counterweight to over-confident strokes-gained
          intuition.
        </p>
        <p>
          <strong>Computing probabilities.</strong> A working scratchpad for
          classic problems — birthday paradox variants, gambler&apos;s ruin,
          Bayesian updating with conjugate priors. Written for the reader, not
          for the grader.
        </p>
      </Section>

      <Section title="Why it&apos;s here">
        <p>
          A portfolio with only shipping products is incomplete. These show how
          I think when the problem is open-ended and there&apos;s no PR to
          merge at the end.
        </p>
      </Section>
    </>
  );
}
