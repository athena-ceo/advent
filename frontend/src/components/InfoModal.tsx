// Copyright (c) 2026 Athena Decisions Systems SAS.
import { useEffect } from "react";

export type InfoKind = "help" | "about";

function Shell({ title, onClose, children }: {
  title: string; onClose: () => void; children: React.ReactNode;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 bg-cave-900/95 flex items-center justify-center p-4"
      onClick={onClose}>
      <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto scroll-thin rounded-lg border border-cave-600 bg-cave-800 shadow-2xl"
        onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 flex items-center justify-between px-5 py-3 border-b border-cave-600 bg-cave-800">
          <h2 className="font-serif text-lg text-amber-glow">{title}</h2>
          <button onClick={onClose}
            className="px-3 py-1 rounded border bg-cave-700 border-cave-600 hover:border-amber-glow/60 text-sm">
            Close ✕
          </button>
        </div>
        <div className="px-5 py-4 text-[13px] leading-relaxed text-cave-100 space-y-4">
          {children}
        </div>
      </div>
    </div>
  );
}

const H = ({ children }: { children: React.ReactNode }) =>
  <h3 className="font-serif text-amber-glow/90 text-sm uppercase tracking-wider">{children}</h3>;
const Cmd = ({ children }: { children: React.ReactNode }) =>
  <code className="px-1 py-0.5 rounded bg-cave-900 border border-cave-600 text-amber-glow/90">{children}</code>;

function Help() {
  return (
    <>
      <p>Colossal Cave is a text adventure: you explore an underground world by
        typing what you want to do, and the game describes what happens. The goal
        is to find your way through the cave, collect its treasures, and survive —
        up to <b>350 points</b>.</p>

      <div className="space-y-1">
        <H>Two ways to play</H>
        <p><b>Classic</b> — type terse commands the way the 1977 game expects
          (<Cmd>go west</Cmd>, <Cmd>take lamp</Cmd>). The parser reads only the
          first five letters of each word and at most two words per line.</p>
        <p><b>Guided</b> — just say what you want in plain English
          (“grab the lamp and head into the cave”). A game master interprets it,
          plays the moves for you, and will help if you ask for a hint.</p>
      </div>

      <div className="space-y-1">
        <H>Getting around</H>
        <p>Directions: <Cmd>north</Cmd> <Cmd>south</Cmd> <Cmd>east</Cmd>{" "}
          <Cmd>west</Cmd> (or <Cmd>n</Cmd>/<Cmd>s</Cmd>/<Cmd>e</Cmd>/<Cmd>w</Cmd>),
          plus <Cmd>up</Cmd> <Cmd>down</Cmd> <Cmd>in</Cmd> <Cmd>out</Cmd> and named
          ways like <Cmd>enter</Cmd>.</p>
        <p>Acting: <Cmd>look</Cmd>, <Cmd>inventory</Cmd> (<Cmd>i</Cmd>),{" "}
          <Cmd>take</Cmd>/<Cmd>drop</Cmd> a thing, <Cmd>open</Cmd>,{" "}
          <Cmd>light lamp</Cmd> / <Cmd>lamp on</Cmd>, <Cmd>read</Cmd>,{" "}
          <Cmd>fill</Cmd>, and so on.</p>
      </div>

      <div className="space-y-1">
        <H>Tips</H>
        <ul className="list-disc pl-5 space-y-1">
          <li><b>Light the lamp before you go into the dark.</b> If it’s pitch
            dark, the picture goes black — and you can stumble into a pit and die.</li>
          <li>The panel on the right shows the room, what you’re carrying, and the
            exits. <b>Click any pill</b> to take/drop an item or move.</li>
          <li>Toggle the <b>Map</b> (top bar) for a live map of the cave around you;
            pick an <b>art style</b> from the dropdown.</li>
          <li><b>Save</b> often. And try the magic words — <Cmd>xyzzy</Cmd>,{" "}
            <Cmd>plugh</Cmd> — you’ll see…</li>
        </ul>
      </div>
    </>
  );
}

function About() {
  return (
    <>
      <p><b>Colossal Cave Adventure</b> (known on the old machines simply as{" "}
        <i>ADVENT</i>, because filenames were six characters) is the original
        <b> 350-point</b> version of the first text adventure ever written — the
        ancestor of Zork and of interactive fiction as a whole.</p>

      <div className="space-y-1">
        <H>A little history</H>
        <p>Around 1975–76, <b>Will Crowther</b> — a programmer at BBN who helped
          build the ARPANET, and a serious caver — wrote the original in
          <b> FORTRAN</b> on a <b>PDP-10</b>. Its passages were modeled on parts of
          Kentucky’s <b>Mammoth Cave</b>, which he had surveyed, with a dash of
          <i> Dungeons &amp; Dragons</i>. In <b>1977</b>, <b>Don Woods</b> at
          Stanford found the program, reached Crowther for the source, and expanded
          it into the fantasy game with its scoring and treasures.</p>
        <p>It spread across the ARPANET and shaped everything that followed. Its
          phrases are folklore now: <i>“you are in a maze of twisty little
          passages, all alike”</i>, and the magic words <Cmd>xyzzy</Cmd> and{" "}
          <Cmd>plugh</Cmd>.</p>
      </div>

      <div className="space-y-1">
        <H>This edition</H>
        <p>This is a faithful, from-scratch port of Crowther &amp; Woods’ original
          <Cmd>advent.for</Cmd> + <Cmd>advent.dat</Cmd> to Python — the game logic
          preserved essentially line-for-line — wrapped in a modern interface:</p>
        <ul className="list-disc pl-5 space-y-1">
          <li>Every location illustrated by <b>AI image models running locally</b>,
            in your choice of art style;</li>
          <li>objects and creatures <b>composited onto the scenes</b> as you meet them;</li>
          <li>a <b>Guided</b> mode that lets you play in plain English via Claude;</li>
          <li>a cave <b>map</b> generated straight from the game’s own travel table.</li>
        </ul>
        <p>The whole modernization was built through <b>AI pair-programming with
          Claude</b> — a 1970s mainframe classic, re-lit for today.</p>
      </div>

      <div className="space-y-1">
        <H>A personal note</H>
        <p>I started programming in high school around <b>1979</b>, after getting
          access to the University of Toledo’s computers in Toledo, Ohio. One of
          the first things I stumbled onto was a PDP-11 FORTRAN version of{" "}
          <i>Adventure</i> — my very first computer game. I got hold of the source,
          taught myself FORTRAN to read it, and spent weeks poring over the data
          file, converting it by hand into a drawn map of Colossal Cave. It was my
          first computer love.</p>
        <p>Ever since AI coding arrived, I’d wondered whether I could finally
          modernize that old code — if only I could find it in a repository
          somewhere. I found it, and now it’s done. The hand-drawn map I labored
          over as a teenager is now generated automatically from the same data
          file, and every room is brought to life. — <i>Harley</i></p>
      </div>
    </>
  );
}

export function InfoModal({ kind, onClose }: { kind: InfoKind; onClose: () => void }) {
  return (
    <Shell title={kind === "help" ? "How to play" : "About Colossal Cave"} onClose={onClose}>
      {kind === "help" ? <Help /> : <About />}
    </Shell>
  );
}
