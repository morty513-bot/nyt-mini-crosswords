type SiteNavProps = {
  current: 'generate' | 'play';
};

export default function SiteNav({ current }: SiteNavProps) {
  return (
    <header className="site-nav">
      <a className="site-brand" href="/nyt-mini-crosswords/">
        NYT Mini Crosswords
      </a>
      <nav className="site-tabs" aria-label="Primary">
        <a
          className={current === 'generate' ? 'site-tab site-tab-active' : 'site-tab'}
          href="/nyt-mini-crosswords/"
        >
          Generate
        </a>
        <a
          className={current === 'play' ? 'site-tab site-tab-active' : 'site-tab'}
          href="/nyt-mini-crosswords/play"
        >
          Play demo
        </a>
      </nav>
    </header>
  );
}
