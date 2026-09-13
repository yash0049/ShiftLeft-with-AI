/**
 * TEMPORARY -- DELETE THIS FILE.
 *
 * Deliberately insecure code, added only to prove that the Semgrep job in
 * .github/workflows/ci.yml really does report findings, and fails the build on
 * high-severity ones. It is expected to turn CI red.
 *
 * Nothing imports this module, so none of it ever runs and none of it ends up
 * in the production bundle.
 *
 * To remove it, revert the commit that added it:
 *
 *     git revert <that commit>
 *
 * or delete the two canary files by hand:
 *
 *     rm backend/_semgrep_canary.py frontend/src/_semgrep_canary.jsx
 */

/** Plaintext HTTP request -- Semgrep `react-insecure-request` (ERROR). */
export function fetchOverPlaintext() {
  return fetch('http://api.example.com/vulnerabilities')
}

/** eval over a URL-controlled value -- Semgrep `detect-eval-with-expression`. */
export function evaluateFragment() {
  return eval(location.hash)
}

/** Unescaped markup from caller input -- Semgrep `react-dangerouslysetinnerhtml`. */
export function RawHtml({ untrustedHtml }) {
  return <div dangerouslySetInnerHTML={{ __html: untrustedHtml }} />
}
