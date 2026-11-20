(() => {
  const area = document.getElementById("message");
  const count = document.getElementById("count");
  const clearBtn = document.getElementById("clearBtn");
  const form = document.getElementById("scanForm");
  const scanBtn = document.getElementById("scanBtn");

  if (area && count) {
    const updateCount = () => {
      count.textContent = `${area.value.length.toLocaleString()} / 10,000`;
      count.classList.toggle("near-limit", area.value.length > 9000);
    };
    area.addEventListener("input", updateCount);
    updateCount();
    if (clearBtn) clearBtn.addEventListener("click", () => {
      area.value = ""; updateCount(); area.focus();
    });
    document.querySelectorAll("[data-sample]").forEach(button => {
      button.addEventListener("click", () => {
        const samples = {
          genuine: "ABC Technologies is inviting applications for a Software Developer Internship. Candidates should know basic Python, HTML and SQL. The internship lasts three months and includes a technical interview. Apply through the careers page on the official company website. No registration or training fee is required.",
          suspicious: "Congratulations! You are selected for a work from home data entry job without an interview. Earn ₹50,000 per month by working only two hours daily. Pay ₹999 as a registration fee immediately to confirm your job. Limited slots available. Send your Aadhaar details and bank information now."
        };
        area.value = samples[button.dataset.sample] || "";
        updateCount(); area.focus();
      });
    });
  }

  if (form && scanBtn) {
    form.addEventListener("submit", () => {
      scanBtn.disabled = true;
      scanBtn.querySelector("span").textContent = "Analysing message...";
      scanBtn.classList.add("loading");
    });
  }
})();
