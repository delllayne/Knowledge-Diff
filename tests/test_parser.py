from knowdiff.parser import extract_page, parse_sections


def test_extracts_title_from_title_tag() -> None:
    html = """
    <html>
      <head><title>React useEffect</title></head>
      <body><main><h1>useEffect</h1><p>Hook docs.</p></main></body>
    </html>
    """
    parsed = extract_page(html, "https://example.com")
    assert parsed.title == "React useEffect"


def test_removes_nav_footer_and_script_content() -> None:
    html = """
    <html>
      <body>
        <nav>Navigation</nav>
        <main>
          <h1>Title</h1>
          <p>Keep me.</p>
        </main>
        <footer>Footer text</footer>
        <script>console.log('ignore')</script>
      </body>
    </html>
    """
    parsed = extract_page(html, "https://example.com")
    assert "Navigation" not in parsed.raw_text
    assert "Footer text" not in parsed.raw_text
    assert "ignore" not in parsed.raw_text
    assert "Keep me." in parsed.raw_text


def test_parses_h1_h2_h3_sections() -> None:
    html = """
    <main>
      <h1>Top</h1>
      <p>Overview</p>
      <h2>Middle</h2>
      <p>Details</p>
      <h3>Deep</h3>
      <p>Notes</p>
    </main>
    """
    sections = parse_sections(html)
    assert [section.heading for section in sections] == ["Top", "Middle", "Deep"]
    assert [section.level for section in sections] == [1, 2, 3]


def test_fallback_when_no_headings_exist() -> None:
    sections = parse_sections("<div><p>Plain text only.</p></div>")
    assert len(sections) == 1
    assert sections[0].heading == "Untitled"
    assert sections[0].text == "Plain text only."


def test_extracts_title_from_heading_when_title_missing() -> None:
    html = """
    <html>
      <body>
        <article>
          <h1>Heading Title</h1>
          <section><p>Body copy</p></section>
        </article>
      </body>
    </html>
    """
    parsed = extract_page(html, "https://example.com")
    assert parsed.title == "Heading Title"


def test_parse_sections_collects_nested_content_until_next_heading() -> None:
    html = """
    <main>
      <h1>Intro</h1>
      <section><p>Paragraph one.</p><ul><li>Bullet</li></ul></section>
      <h2>Next</h2>
      <div><p>Paragraph two.</p></div>
    </main>
    """
    sections = parse_sections(html)
    assert sections[0].text == "Paragraph one.\nBullet"
    assert sections[1].text == "Paragraph two."
