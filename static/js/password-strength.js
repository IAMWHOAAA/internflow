(() => {
  const form = document.querySelector("[data-password-form]");
  if (!form) return;

  const password = form.querySelector("#id_password1");
  const confirmation = form.querySelector("#id_password2");
  const audit = form.querySelector("[data-password-audit]");
  const label = form.querySelector("[data-strength-label]");
  const bars = [...form.querySelectorAll(".strength-bars i")];
  const matchIndicator = form.querySelector("[data-match-indicator]");
  const toggle = form.querySelector("[data-toggle-password]");
  const commonPasswords = new Set([
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "abc12345",
    "admin123",
  ]);

  const setRule = (name, passed) => {
    const element = audit.querySelector(`[data-rule="${name}"]`);
    element.classList.toggle("passed", passed);
    element.querySelector("i").textContent = passed ? "✓" : "○";
  };

  const update = () => {
    const value = password.value;
    const rules = {
      length: value.length >= 8,
      letter: /[A-Za-z]/.test(value),
      number: /\d/.test(value),
      common: value.length > 0 && !commonPasswords.has(value.toLowerCase()),
    };
    Object.entries(rules).forEach(([name, passed]) => setRule(name, passed));

    const hasMixedCase = /[a-z]/.test(value) && /[A-Z]/.test(value);
    const hasSymbol = /[^A-Za-z0-9]/.test(value);
    let level = 0;
    if (value) {
      if (!rules.length || !rules.letter || !rules.number || !rules.common) {
        level = 1;
      } else if (value.length < 10) {
        level = 2;
      } else if (value.length >= 12 && (hasMixedCase || hasSymbol)) {
        level = 4;
      } else {
        level = 3;
      }
    }

    const labels = ["等待输入", "较弱", "一般", "良好", "很强"];
    const classes = ["empty", "weak", "fair", "good", "strong"];
    audit.dataset.level = classes[level];
    label.textContent = labels[level];
    bars.forEach((bar, index) => bar.classList.toggle("active", index < level));

    const hasConfirmation = confirmation.value.length > 0;
    const matches = hasConfirmation && value === confirmation.value;
    matchIndicator.textContent = hasConfirmation ? (matches ? "✓ 两次密码一致" : "× 密码不一致") : "";
    matchIndicator.classList.toggle("matched", matches);
    matchIndicator.classList.toggle("mismatched", hasConfirmation && !matches);
  };

  password.addEventListener("input", update);
  confirmation.addEventListener("input", update);
  toggle.addEventListener("click", () => {
    const isPassword = password.type === "password";
    password.type = isPassword ? "text" : "password";
    toggle.setAttribute("aria-label", isPassword ? "隐藏密码" : "显示密码");
    toggle.classList.toggle("revealed", isPassword);
  });
  update();
})();
