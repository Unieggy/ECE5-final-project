/* ════════════════════════════════════════════════════════════════════════════
   Lebron GPT — script.js
   ════════════════════════════════════════════════════════════════════════════ */

const LEBRON_GIF = 'https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExeHV3OTl2bnd5amwzcHRsNnk3cmt6dXR5eWFpZ3V0aHdpNmpwa2VnNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/Rt3sQAPAfahuTnHaMi/giphy.gif';

// ── Button escalation ──────────────────────────────────────────────────────

let clickCount = 0;

const BTN_LABELS = [
  'Deploy Lebron',
  'Deploy More?',
  'He Keeps Coming',
  'You Asked For This',
  'KING JAMES MODE',
];

function deployLebron() {
  clickCount++;

  const btn = document.getElementById('deployBtn');
  const labelIndex = Math.min(clickCount, BTN_LABELS.length - 1);
  btn.innerHTML = BTN_LABELS[labelIndex];

  // Show remove button after first deploy
  document.getElementById('removeBtn').style.display = 'block';

  // Escalate: more LeBrons each click, cap at 18
  const count = Math.min(5 + clickCount * 2, 18);

  for (let i = 0; i < count; i++) {
    setTimeout(() => spawnLebron(), i * 90);
  }
}

function removeLebrons() {
  document.querySelectorAll('.lebron').forEach((el) => el.remove());
  clickCount = 0;
  document.getElementById('deployBtn').innerHTML = BTN_LABELS[0];
  document.getElementById('removeBtn').style.display = 'none';
}

// ── Spawn a single LeBron ──────────────────────────────────────────────────

function spawnLebron() {
  const hero = document.querySelector('.hero');
  const img  = document.createElement('img');
  img.src    = LEBRON_GIF;
  img.alt    = 'LeBron James';
  img.className = 'lebron';

  // Random horizontal position within the hero width
  const heroW  = hero.offsetWidth;
  const left   = Math.random() * (heroW - 90);

  // Land in the bottom third of the hero — below the title/buttons
  const heroH  = hero.offsetHeight;
  const landY  = heroH * 0.65 + Math.random() * heroH * 0.25;

  // Random scale + random horizontal flip for variety
  const scale  = 0.75 + Math.random() * 0.55;
  const flipX  = Math.random() < 0.5 ? 1 : -1;

  img.style.cssText = `left:${left}px; top:-90px; transform:scaleX(${flipX}) scale(${scale});`;

  hero.appendChild(img);

  // Animate: fall → overshoot → tiny bounce → settle
  img.animate(
    [
      { top: '-90px',             easing: 'ease-in'  },
      { top: `${landY - 18}px`,   easing: 'ease-out', offset: 0.72 },
      { top: `${landY + 10}px`,   easing: 'ease-in',  offset: 0.86 },
      { top: `${landY - 5}px`,    easing: 'ease-out', offset: 0.93 },
      { top: `${landY}px` },
    ],
    { duration: 850 + Math.random() * 450, fill: 'forwards' }
  );
}

// ── Scroll reveal ──────────────────────────────────────────────────────────

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.08 }
);

document.querySelectorAll('.section').forEach((el) => revealObserver.observe(el));
