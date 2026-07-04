/* @ds-bundle: {"format":4,"namespace":"VoltAgentDesignSystem_438fa2","components":[{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"CodeBlock","sourcePath":"components/core/CodeBlock.jsx"},{"name":"CodeChip","sourcePath":"components/core/CodeChip.jsx"},{"name":"Input","sourcePath":"components/core/Input.jsx"},{"name":"NavBar","sourcePath":"components/core/NavBar.jsx"}],"sourceHashes":{"components/core/Badge.jsx":"9217d45c3b2e","components/core/Button.jsx":"b9309cb732ed","components/core/Card.jsx":"4fed65215702","components/core/CodeBlock.jsx":"60387abb9c26","components/core/CodeChip.jsx":"b3092f8cfe2a","components/core/Input.jsx":"34826bb9745e","components/core/NavBar.jsx":"f818fa06cf1a"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.VoltAgentDesignSystem_438fa2 = window.VoltAgentDesignSystem_438fa2 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Badge.jsx
try { (() => {
/**
 * VoltAgent Badge — inline status pill for live indicators, category tags, and version labels.
 * @param {object} props
 * @param {"green"|"neutral"|"outline"} [props.variant="outline"]
 * @param {React.ReactNode} props.children
 */
function Badge({
  variant = "outline",
  children,
  style = {}
}) {
  const variants = {
    green: {
      background: "rgba(0,217,146,0.12)",
      color: "#00d992",
      border: "1px solid rgba(0,217,146,0.3)"
    },
    neutral: {
      background: "#1a1a1a",
      color: "#bdbdbd",
      border: "1px solid #3d3a39"
    },
    outline: {
      background: "#101010",
      color: "#f2f2f2",
      border: "1px solid #3d3a39"
    }
  };
  const base = {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "12px",
    fontWeight: 500,
    lineHeight: "16px",
    borderRadius: "9999px",
    padding: "4px 10px",
    whiteSpace: "nowrap",
    ...variants[variant],
    ...style
  };
  return /*#__PURE__*/React.createElement("span", {
    style: base
  }, children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
/**
 * VoltAgent Button — primary CTA, outline, ghost-green, and pill-tag variants.
 * @param {object} props
 * @param {"primary"|"outline"|"ghost"|"pill"} [props.variant="primary"]
 * @param {"sm"|"md"} [props.size="md"]
 * @param {boolean} [props.disabled=false]
 * @param {string} [props.href] - renders as <a> if provided
 * @param {React.ReactNode} props.children
 * @param {function} [props.onClick]
 */
function Button({
  variant = "primary",
  size = "md",
  disabled = false,
  href,
  children,
  onClick,
  style = {}
}) {
  const base = {
    display: "inline-flex",
    alignItems: "center",
    gap: "8px",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: size === "sm" ? "14px" : "16px",
    fontWeight: 600,
    lineHeight: size === "sm" ? "20px" : "24px",
    textDecoration: "none",
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.45 : 1,
    border: "none",
    outline: "none",
    transition: "opacity 150ms ease, box-shadow 150ms ease",
    whiteSpace: "nowrap"
  };
  const variants = {
    primary: {
      background: "#00d992",
      color: "#101010",
      border: "none",
      borderRadius: "6px",
      padding: size === "sm" ? "8px 12px" : "12px 16px"
    },
    outline: {
      background: "#101010",
      color: "#f2f2f2",
      border: "1px solid #3d3a39",
      borderRadius: "6px",
      padding: size === "sm" ? "8px 12px" : "12px 16px"
    },
    ghost: {
      background: "transparent",
      color: "#2fd6a1",
      border: "none",
      borderRadius: "6px",
      padding: size === "sm" ? "8px 12px" : "12px 16px"
    },
    pill: {
      background: "#101010",
      color: "#f2f2f2",
      border: "1px solid #3d3a39",
      borderRadius: "9999px",
      padding: "4px 12px",
      fontSize: "14px",
      fontWeight: 400,
      lineHeight: "20px"
    }
  };
  const merged = {
    ...base,
    ...variants[variant],
    ...style
  };
  if (href) {
    return /*#__PURE__*/React.createElement("a", {
      href: href,
      style: merged
    }, children);
  }
  return /*#__PURE__*/React.createElement("button", {
    style: merged,
    disabled: disabled,
    onClick: onClick,
    onMouseEnter: e => {
      if (!disabled) e.currentTarget.style.opacity = "0.85";
    },
    onMouseLeave: e => {
      e.currentTarget.style.opacity = disabled ? "0.45" : "1";
    }
  }, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
/**
 * VoltAgent Card — feature card with hairline border on dark canvas.
 * @param {object} props
 * @param {"default"|"emphasized"|"featured"} [props.variant="default"]
 * @param {React.ReactNode} props.children
 * @param {string} [props.style]
 */
function Card({
  variant = "default",
  children,
  style = {},
  onClick
}) {
  const borders = {
    default: "1px solid #3d3a39",
    emphasized: "3px solid #3d3a39",
    featured: "2px solid #00d992"
  };
  const base = {
    background: "#101010",
    border: borders[variant] || borders.default,
    borderRadius: "8px",
    padding: "24px",
    color: "#f2f2f2",
    fontFamily: "Inter, system-ui, sans-serif",
    transition: "box-shadow 150ms ease",
    cursor: onClick ? "pointer" : "default",
    ...style
  };
  return /*#__PURE__*/React.createElement("div", {
    style: base,
    onClick: onClick,
    onMouseEnter: e => {
      e.currentTarget.style.boxShadow = "0 0 15px rgba(92,88,85,0.2)";
    },
    onMouseLeave: e => {
      e.currentTarget.style.boxShadow = "none";
    }
  }, children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/CodeBlock.jsx
try { (() => {
/**
 * VoltAgent CodeBlock — dark code-editor card with SF Mono / JetBrains Mono and optional filename header.
 * @param {object} props
 * @param {string} [props.filename] - shown in header bar
 * @param {string} [props.language]
 * @param {string} props.code - raw code string (whitespace preserved)
 */
function CodeBlock({
  filename,
  code,
  children,
  style = {}
}) {
  const [copied, setCopied] = React.useState(false);
  function handleCopy() {
    const text = code || (typeof children === "string" ? children : "");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }
  const containerStyle = {
    background: "#1a1a1a",
    border: "1px solid #3d3a39",
    borderRadius: "8px",
    overflow: "hidden",
    fontFamily: "'JetBrains Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    fontSize: "13px",
    lineHeight: "18px",
    color: "#f5f6f7",
    ...style
  };
  const headerStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 16px",
    borderBottom: "1px solid #3d3a39",
    background: "#101010"
  };
  const bodyStyle = {
    padding: "20px",
    overflowX: "auto",
    whiteSpace: "pre"
  };
  const copyBtnStyle = {
    background: "none",
    border: "none",
    color: copied ? "#00d992" : "#8b949e",
    cursor: "pointer",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "12px",
    fontWeight: 500,
    padding: "0",
    transition: "color 150ms ease"
  };
  return /*#__PURE__*/React.createElement("div", {
    style: containerStyle
  }, filename !== undefined && /*#__PURE__*/React.createElement("div", {
    style: headerStyle
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "#8b949e",
      fontSize: "12px",
      fontFamily: "Inter, sans-serif"
    }
  }, filename || ""), /*#__PURE__*/React.createElement("button", {
    style: copyBtnStyle,
    onClick: handleCopy
  }, copied ? "Copied!" : "Copy")), /*#__PURE__*/React.createElement("div", {
    style: bodyStyle
  }, code || children));
}
Object.assign(__ds_scope, { CodeBlock });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/CodeBlock.jsx", error: String((e && e.message) || e) }); }

// components/core/CodeChip.jsx
try { (() => {
/**
 * VoltAgent CodeChip — inline monospace code snippet pill (e.g. `npx create-voltagent-app`).
 * @param {object} props
 * @param {React.ReactNode} props.children
 */
function CodeChip({
  children,
  style = {}
}) {
  return /*#__PURE__*/React.createElement("code", {
    style: {
      fontFamily: "'JetBrains Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace",
      fontSize: "13px",
      fontWeight: 400,
      lineHeight: "18px",
      background: "#1a1a1a",
      color: "#f5f6f7",
      borderRadius: "6px",
      padding: "2px 8px",
      display: "inline",
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { CodeChip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/CodeChip.jsx", error: String((e && e.message) || e) }); }

// components/core/Input.jsx
try { (() => {
/**
 * VoltAgent Input — standard text input on dark canvas.
 * @param {object} props
 * @param {string} [props.placeholder]
 * @param {string} [props.type="text"]
 * @param {string} [props.value]
 * @param {function} [props.onChange]
 * @param {boolean} [props.disabled]
 * @param {string} [props.label]
 */
function Input({
  placeholder,
  type = "text",
  value,
  onChange,
  disabled = false,
  label,
  style = {}
}) {
  const [focused, setFocused] = React.useState(false);
  const inputStyle = {
    display: "block",
    width: "100%",
    background: "#1a1a1a",
    color: "#f2f2f2",
    border: focused ? "1px solid #00d992" : "1px solid #3d3a39",
    borderRadius: "6px",
    padding: "12px 16px",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "14px",
    fontWeight: 400,
    lineHeight: "20px",
    outline: "none",
    transition: "border-color 150ms ease",
    opacity: disabled ? 0.45 : 1,
    cursor: disabled ? "not-allowed" : "text",
    boxSizing: "border-box",
    ...style
  };
  const labelStyle = {
    display: "block",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "12px",
    fontWeight: 500,
    lineHeight: "16px",
    color: "#8b949e",
    marginBottom: "6px"
  };
  return /*#__PURE__*/React.createElement("div", null, label && /*#__PURE__*/React.createElement("label", {
    style: labelStyle
  }, label), /*#__PURE__*/React.createElement("input", {
    type: type,
    placeholder: placeholder,
    value: value,
    onChange: onChange,
    disabled: disabled,
    style: inputStyle,
    onFocus: () => setFocused(true),
    onBlur: () => setFocused(false)
  }));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Input.jsx", error: String((e && e.message) || e) }); }

// components/core/NavBar.jsx
try { (() => {
/**
 * VoltAgent NavBar — sticky dark top navigation with logo, links, and CTA.
 * @param {object} props
 * @param {string} [props.logoText="VoltAgent"] - brand name text
 * @param {Array<{label:string,href:string}>} [props.links]
 * @param {string} [props.ctaLabel="Get started"]
 * @param {string} [props.ctaHref="#"]
 */
function NavBar({
  logoText = "VoltAgent",
  links = [],
  ctaLabel = "Get started",
  ctaHref = "#"
}) {
  const navStyle = {
    position: "sticky",
    top: 0,
    zIndex: 100,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    background: "#101010",
    borderBottom: "1px solid #3d3a39",
    padding: "12px 32px",
    fontFamily: "Inter, system-ui, sans-serif"
  };
  const logoStyle = {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    color: "#f2f2f2",
    textDecoration: "none",
    fontSize: "16px",
    fontWeight: 600,
    lineHeight: "24px"
  };
  const linksStyle = {
    display: "flex",
    alignItems: "center",
    gap: "24px",
    listStyle: "none",
    margin: 0,
    padding: 0
  };
  const linkStyle = {
    color: "#bdbdbd",
    textDecoration: "none",
    fontSize: "14px",
    fontWeight: 400,
    lineHeight: "20px",
    transition: "color 150ms ease"
  };
  const ctaStyle = {
    display: "inline-flex",
    alignItems: "center",
    background: "#00d992",
    color: "#101010",
    border: "none",
    borderRadius: "6px",
    padding: "8px 14px",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "14px",
    fontWeight: 600,
    lineHeight: "20px",
    textDecoration: "none",
    cursor: "pointer",
    transition: "opacity 150ms ease"
  };
  return /*#__PURE__*/React.createElement("nav", {
    style: navStyle
  }, /*#__PURE__*/React.createElement("a", {
    href: "/",
    style: logoStyle
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "#00d992",
      fontSize: "18px"
    }
  }, "\u26A1"), logoText), /*#__PURE__*/React.createElement("ul", {
    style: linksStyle
  }, links.map((l, i) => /*#__PURE__*/React.createElement("li", {
    key: i
  }, /*#__PURE__*/React.createElement("a", {
    href: l.href,
    style: linkStyle,
    onMouseEnter: e => e.target.style.color = "#f2f2f2",
    onMouseLeave: e => e.target.style.color = "#bdbdbd"
  }, l.label)))), /*#__PURE__*/React.createElement("a", {
    href: ctaHref,
    style: ctaStyle,
    onMouseEnter: e => e.currentTarget.style.opacity = "0.85",
    onMouseLeave: e => e.currentTarget.style.opacity = "1"
  }, ctaLabel));
}
Object.assign(__ds_scope, { NavBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/NavBar.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.CodeBlock = __ds_scope.CodeBlock;

__ds_ns.CodeChip = __ds_scope.CodeChip;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.NavBar = __ds_scope.NavBar;

})();
