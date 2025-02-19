# Do’s and Don’ts for Taking a Figma Design to HTML & CSS

Below is a refined **Do’s and Don’ts** list specifically focused on preparing a Figma design for export to HTML and CSS (whether manually or via plugins/tools). This helps new Figma users structure and name their designs in a developer-friendly way, ensuring a smoother handoff and more maintainable front-end code.

---

## Do’s

1. **Start With Well-Organized Frames & Layers**  
   - Treat each major section (header, footer, main content) as its own frame or group.  
   - This structure translates more cleanly to HTML `<header>`, `<main>`, `<footer>`, etc.

2. **Use Consistent Naming Conventions**  
   - Label layers, groups, and components with meaningful names (e.g., `Button/Primary`, `Card/Product`, `Header/Nav`).  
   - Developers often translate these names directly into CSS classes or component names.

3. **Leverage Auto Layout for Responsive Design**  
   - Auto Layout in Figma mimics **flexbox** behavior in CSS.  
   - Mastering Auto Layout helps predict how elements might resize or shift in different breakpoints.

4. **Define Text & Color Styles (Design Tokens)**  
   - Create and consistently use text styles for headings, body text, captions, etc.  
   - Establish color styles (e.g., `Color/Primary`, `Color/Secondary`) that map well to CSS variables (e.g., `--color-primary`).

5. **Check Constraints & Responsive Behavior Early**  
   - Use Figma’s “Constraints” feature to ensure elements resize correctly for different screen sizes.  
   - Minimizes rework when implementing responsive CSS later.

6. **Use the Inspect Panel for CSS Snippets**  
   - Figma’s “Inspect” panel shows size, spacing, and provides basic CSS snippets (font-size, color, etc.).  
   - Great reference for developers, especially when translating designs to code.

7. **Optimize and Export Assets Properly**  
   - For images or icons, export them at the correct resolution and format (`.png`, `.jpg`, `.svg`) for web usage.  
   - Use Figma’s export settings (1x, 2x, etc.) or relevant plugins to keep file sizes small.

8. **Use Plugins or Third-Party Tools Strategically**  
   - Explore plugins like “Figma to HTML/CSS” or “HTML Generator” for a quick code scaffold.  
   - **Always** review and clean up the auto-generated code afterward.

9. **Document Design Decisions (Comments & Notes)**  
   - Include notes on spacing, font usage, and interactions where it matters most.  
   - Ensures developers have context for translating the design into clean, semantic HTML/CSS.

10. **Collaborate with Developers Early**  
   - Share your Figma file and get feedback on feasibility.  
   - Early collaboration reduces rework and ensures a smoother handoff.

---

## Don’ts

1. **Don’t Flatten or Over-Group Layers**  
   - Flattening everything or grouping all elements into one group makes it tough to see the structure.  
   - Keep layers logically nested to reflect how they’d be structured in HTML.

2. **Don’t Rely Solely on Auto-Generated Code**  
   - Plugins that convert designs to HTML/CSS can be a starting point but often produce bloated or non-semantic code.  
   - Review, refactor, and ensure semantic tags (`<nav>`, `<section>`, `<footer>`) are used.

3. **Don’t Overlook Browser & Device Constraints**  
   - Designing only for a large desktop frame can lead to issues on mobile or tablet.  
   - Test responsive frames and apply constraints for adaptive layouts.

4. **Don’t Skip Naming Your Components & Styles**  
   - Leaving components named “Component 1” or colors as default hex codes confuses everyone.  
   - Meaningful naming streamlines mapping to CSS variables or class names.

5. **Don’t Neglect Proper Spacing & Alignment**  
   - Inconsistent spacing or sloppy alignment results in more complicated CSS.  
   - Use consistent padding, margins, and grids in Figma to reduce guesswork.

6. **Don’t Ignore Image & Asset Optimization**  
   - Large, uncompressed images cause performance issues.  
   - Always optimize or compress images before exporting.

7. **Don’t Abandon Accessibility Considerations**  
   - Figma supports labeling for text layers and simulating color contrast.  
   - Maintain color contrast, font size, and readability to simplify meeting accessibility standards.

8. **Don’t Use Absolute Positioning for Everything**  
   - Placing elements without constraints can look fine in Figma but fails in flexible CSS layouts.  
   - Rely on layout settings akin to **flexbox** or **grid** (e.g., Auto Layout).

9. **Don’t Overcomplicate Interactions**  
   - Early on, focus on core flows and keep interactions simple.  
   - Add complex animations or micro-interactions when the main experience is finalized.

10. **Don’t Forget Versioning & Handoff Docs**  
   - If you change design elements after handoff, inform your team or create a new version.  
   - Untracked changes can lead to mismatched design vs. code scenarios.

---

### Key Takeaways
By structuring your layers thoughtfully, using consistent naming, and understanding how Figma’s tools translate to standard HTML/CSS patterns (like flexbox or grid), you set yourself—and your developers—up for success. Keep an eye on file organization, responsiveness, and asset optimization. While plugins and auto-generated code can provide a starting point, **collaboration** and **clear documentation** remain the best ways to ensure a smooth workflow from Figma design to production-ready web pages.
