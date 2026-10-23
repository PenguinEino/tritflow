"""Render submission claims from machine outputs and executed evaluation tables."""

from html.parser import HTMLParser
import re


class Tables(HTMLParser):
    """Read literal table cells without interpreting scripts or computing results."""

    def __init__(self):
        super().__init__()
        self.tables, self.rows, self.row, self.value = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.rows = []
        elif tag == "tr" and self.rows is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.value = []

    def handle_data(self, data):
        if self.value is not None:
            self.value.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.value is not None:
            self.row.append(" ".join("".join(self.value).split()))
            self.value = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "table" and self.rows is not None:
            if self.rows:
                self.tables.append(self.rows)
            self.rows = None


def chapter6(document):
    """Discover future chapter-6 tables by heading, independent of cell IDs."""
    inside, present, executed, records = False, False, [], []
    for cell in document.cells:
        if cell.id.startswith("submission-"):
            continue
        if cell.cell_type == "markdown":
            match = re.search(r"(?m)^##\s+(?:第\s*)?(\d+)(?:[.．、章\s]|$)", cell.source)
            if match:
                inside = int(match[1]) == 6
                present |= inside
        if inside and cell.cell_type == "code":
            if cell.execution_count is None:
                raise ValueError("chapter 6 contains unexecuted code")
            executed.append(cell.id)
            for output in cell.get("outputs", []):
                parser = Tables()
                parser.feed(output.get("data", {}).get("text/html", ""))
                records.extend({"cell_id":cell.id, "rows":rows} for rows in parser.tables)
    return {"present":present, "executed_cell_ids":executed, "tables":records}


def markdown_table(rows):
    width = max(map(len, rows))
    def line(row):
        return "| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ")
                                  for v in row + [""]*(width-len(row))) + " |"
    return "\n".join([line(rows[0]), line(["---"]*width), *(line(row) for row in rows[1:])])


def result_values(evidence, evaluation):
    """Keep exhaustive logic coverage distinct from the sampled analog campaign."""
    designs = evidence.get("designs", {})
    dot = designs.get("dot4", {})
    rows = []
    sentences = []
    if dot:
        report, equivalence = dot["report"], dot["equivalence"]
        cells = report.get("total_cells", sum(report.get("cells", {}).values()))
        if not equivalence.get("passed"):
            raise ValueError("dot4 synthesis equivalence did not pass")
        vectors = equivalence["vectors"]
        rows.append(["Synthesized dot product", f"{cells:,} cells; {vectors:,} logical input vectors checked"])
        sentences.append(f"The running dot product maps to {cells:,} cells and passes synthesis equivalence over {vectors:,} input vectors")
        layout = dot.get("layout", {})
        if "die_size_um" in layout:
            width, height = layout["die_size_um"]
            rows.append(["Routed core dimensions", f"{width:g} × {height:g} µm"])
        drc, lvs = dot.get("drc", {}), dot.get("lvs", {})
        if "violations" in drc:
            if drc["violations"] != 0:
                raise ValueError("dot4 DRC is not clean")
            rows.append(["PDK drawing DRC", f"{drc['violations']} violations"])
        if "matched" in lvs:
            if not lvs["matched"]:
                raise ValueError("dot4 LVS did not match")
            rows.append(["PDK LVS", "Matched"])
        measurements = dot.get("measurements", {})
        if measurements:
            if not measurements.get("passed"):
                raise ValueError("dot4 nominal post-layout level check did not pass")
            segments = len(measurements["rows"])
            rows.append(["Nominal post-layout SPICE", f"{segments} stimulus intervals passed the ±0.5 V output-level check"])
            sentences.append(f"post-layout ngspice passes the output-level check for {segments} stimulus intervals")
            for pin, value in measurements.get("max_settling_s", {}).items():
                if value is None:
                    raise ValueError("a reported output never settled")
                rows.append([f"SPICE maximum settling, {pin}", f"{value*1e9:.1f} ns"])
                if pin in dot.get("sta_arrival_s", {}):
                    rows.append([f"STA estimate, {pin}", f"{dot['sta_arrival_s'][pin]*1e9:.1f} ns"])
    summary = markdown_table([["Executed check", "Result"], *rows]) if rows else "No dot-product result is present in this executed revision."
    sentence = "; ".join(sentences) + "." if sentences else "This executed revision contains no dot-product result."
    tables = evaluation.get("tables", [])
    chapter = "\n\n".join("From executed cell `"+table["cell_id"]+"`:\n\n"+markdown_table(table["rows"])
                             for table in tables)
    if not chapter:
        chapter = ("Chapter 6 executed without a tabular evaluation summary; no scaling or power numbers are quoted here."
                   if evaluation.get("executed_cell_ids") else
                   "This executed revision contains no chapter 6 evaluation; scaling and power results are not reported here.")
    return {"RESULTS":summary, "RESULTS_SENTENCE":sentence, "CHAPTER6_RESULTS":chapter}
