export default function LandingPage() {
  const whatsappNumber = "2348020812523";

  return (
    <div className="min-h-screen bg-[#fdfcf6] text-[#10202d]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@600;700;800&family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');
        .material-symbols-outlined {
          font-variation-settings: 'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 24;
          display: inline-block;
          line-height: 1;
          vertical-align: middle;
        }
        html { scroll-behavior: smooth; }
      `}</style>

      <header className="sticky top-0 z-50 border-b border-white/70 bg-white/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-10">
          <a href="#top" className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-[#0a6a3c] text-white shadow-lg shadow-black/10">
              <span className="material-symbols-outlined">savings</span>
            </div>
            <div>
              <div className="font-['Hanken_Grotesk'] text-lg font-bold leading-none text-[#0a6a3c]">SabiSpend</div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-[#51606e]">WhatsApp money assistant</div>
            </div>
          </a>
          <nav className="hidden items-center gap-8 text-sm font-semibold text-[#51606e] md:flex">
            <a href="#how-it-works" className="hover:text-[#0a6a3c]">How it works</a>
            <a href="#features" className="hover:text-[#0a6a3c]">Features</a>
            <a href="#security" className="hover:text-[#0a6a3c]">Security</a>
            <a href="#faq" className="hover:text-[#0a6a3c]">FAQ</a>
          </nav>
          <a href={`https://wa.me/${whatsappNumber}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-full bg-[#0a6a3c] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-black/10 transition hover:bg-[#064927]">
            <span className="material-symbols-outlined text-[18px]">chat</span>
            Chat on WhatsApp
          </a>
        </div>
      </header>

      <main id="top">
        <section className="mx-auto grid max-w-7xl items-center gap-14 px-5 pb-14 pt-14 lg:grid-cols-[1.08fr_0.92fr] lg:px-10 lg:pb-20 lg:pt-20">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-[#0a6a3c]/8 px-4 py-2 text-xs font-bold uppercase tracking-[0.24em] text-[#0a6a3c]">
              WhatsApp-native
              <span className="h-1.5 w-1.5 rounded-full bg-[#25d366]" />
              No app needed
            </div>
            <h1 className="mt-6 font-['Hanken_Grotesk'] text-4xl font-bold leading-tight text-[#10202d] sm:text-5xl lg:text-6xl">
              Understand Your Money.
              <span className="block text-[#0a6a3c]">Grow Your Savings.</span>
              All on WhatsApp.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-[#51606e]">
              Built for market women, traders, and small business owners. Send receipts, speak in your language, and get clear money advice without stress.
            </p>
            <div className="mt-8 flex flex-col gap-4 sm:flex-row">
              <a href={`https://wa.me/${whatsappNumber}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center gap-3 rounded-full bg-[#0a6a3c] px-6 py-4 text-sm font-bold text-white shadow-lg shadow-black/10 transition hover:-translate-y-0.5 hover:bg-[#064927]">
                <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                Start on WhatsApp
              </a>
              <a href="#features" className="inline-flex items-center justify-center gap-3 rounded-full border-2 border-[#0a6a3c]/25 bg-white px-6 py-4 text-sm font-bold text-[#0a6a3c] transition hover:border-[#0a6a3c] hover:bg-[#0a6a3c]/5">
                Watch Demo
              </a>
            </div>
            <div className="mt-8 flex flex-wrap gap-3 text-sm font-semibold text-[#51606e]">
              <span className="rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-[#d5dfec]">Pidgin • Yoruba • Hausa • Igbo</span>
              <span className="rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-[#d5dfec]">Receipt scanning</span>
              <span className="rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-[#d5dfec]">Scam checks</span>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-md">
            <div className="absolute -left-8 top-8 h-28 w-28 rounded-full bg-[#25d366]/15 blur-3xl" />
            <div className="absolute -right-8 bottom-6 h-32 w-32 rounded-full bg-[#0a6a3c]/15 blur-3xl" />
            <div className="relative rounded-[2.5rem] bg-[#0f2030] p-3 shadow-[0_30px_80px_rgba(9,20,31,.25)]">
              <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-[#f4eadf]">
                <img src="/assets/sabi-main-screen.png" alt="SabiSpend WhatsApp dashboard mockup" className="block h-auto w-full" />
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-[#0a6a3c]/10 bg-[#0a6a3c] text-white">
          <div className="mx-auto max-w-7xl overflow-hidden px-5 py-4 lg:px-10">
            <div className="flex w-max animate-[marquee_26s_linear_infinite] items-center gap-10 text-sm font-bold uppercase tracking-[0.18em]">
              <span className="flex items-center gap-2"><span className="material-symbols-outlined">verified</span> 200+ Nigerian foods recognized</span>
              <span className="flex items-center gap-2"><span className="material-symbols-outlined">security</span> BMONI secure wallets</span>
              <span className="flex items-center gap-2"><span className="material-symbols-outlined">translate</span> Pidgin • Yoruba • Hausa • Igbo</span>
              <span className="flex items-center gap-2"><span className="material-symbols-outlined">qr_code_2</span> Works on WhatsApp only</span>
              <span className="flex items-center gap-2"><span className="material-symbols-outlined">verified</span> 200+ Nigerian foods recognized</span>
              <span className="flex items-center gap-2"><span className="material-symbols-outlined">security</span> BMONI secure wallets</span>
            </div>
          </div>
        </section>

        <section id="features" className="mx-auto max-w-7xl px-5 py-20 lg:px-10">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-bold uppercase tracking-[0.26em] text-[#0a6a3c]">The SabiSpend Difference</p>
            <h2 className="mt-3 font-['Hanken_Grotesk'] text-3xl font-bold text-[#10202d] sm:text-4xl">Designed for your daily hustle</h2>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {[
              { icon: 'mic', title: 'Voice & Photo First', body: 'No typing needed. Speak naturally or snap a receipt and let SabiSpend do the reading.', tone: 'bg-[#0a6a3c]/10 text-[#0a6a3c]' },
              { icon: 'trending_up', title: 'Daily Profit Helper', body: 'See what you made today, what you spent, and how close you are to your savings goal.', tone: 'bg-[#25d366]/10 text-[#0a6a3c]' },
              { icon: 'gpp_maybe', title: 'Scam Checker', body: 'Forward suspicious messages or links and get a clear warning before you lose money.', tone: 'bg-[#dc2626]/10 text-[#dc2626]' },
              { icon: 'account_balance_wallet', title: 'Safe Savings', body: 'Guided saving for rent, stock, or school fees, backed by BMONI secure wallets.', tone: 'bg-[#e5eeff] text-[#0a6a3c]' }
            ].map((feature) => (
              <article key={feature.title} className="rounded-[1.5rem] border border-[#d5dfec] bg-white p-6 shadow-sm">
                <div className={`mb-5 grid h-12 w-12 place-items-center rounded-2xl ${feature.tone}`}>
                  <span className="material-symbols-outlined">{feature.icon}</span>
                </div>
                <h3 className="font-['Hanken_Grotesk'] text-xl font-bold">{feature.title}</h3>
                <p className="mt-3 text-sm leading-7 text-[#51606e]">{feature.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="how-it-works" className="bg-[#12202e] text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[0.95fr_1.05fr] lg:px-10">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.26em] text-[#87d8a2]">How it works</p>
              <h2 className="mt-3 font-['Hanken_Grotesk'] text-3xl font-bold sm:text-4xl">Start Sabi-ing in 4 simple steps</h2>
              <div className="mt-10 space-y-8">
                {[
                  ['1', 'Send a message', 'Say hi or send a voice note to the WhatsApp number. No password needed.'],
                  ['2', 'Link your wallet', 'We help you connect a secure BMONI wallet in a few guided steps.'],
                  ['3', 'Send photos or speak', 'Capture daily sales, stock, or expenses and let the assistant organize them.'],
                  ['4', 'Get advice', 'Receive simple profit summaries and practical saving tips every day.']
                ].map(([step, title, body]) => (
                  <div key={step} className="flex gap-4">
                    <div className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-[#0a6a3c] text-white font-bold">{step}</div>
                    <div>
                      <h3 className="font-['Hanken_Grotesk'] text-xl font-bold">{title}</h3>
                      <p className="mt-2 text-sm leading-7 text-white/75">{body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <img src="/assets/sabi-image1.png" alt="Money counting scene" className="h-64 w-full rounded-[1.8rem] object-cover shadow-lg shadow-black/10" />
              <img src="/assets/sabi-image2.png" alt="Money counting scene variant" className="h-64 w-full rounded-[1.8rem] object-cover shadow-lg shadow-black/10" />
              <img src="/assets/sabi-image3.png" alt="Feature badges for scam alert and smart AI" className="h-72 w-full rounded-[1.8rem] bg-white object-cover p-3 shadow-lg shadow-black/10" />
              <img src="/assets/sabi-image4.png" alt="Secure and trusted BMONI badge" className="h-72 w-full rounded-[1.8rem] bg-white object-contain p-4 shadow-lg shadow-black/10" />
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 py-20 lg:px-10">
          <div className="grid gap-6 rounded-[2rem] bg-[#bdf8c7] px-6 py-10 text-center shadow-lg shadow-black/5 lg:grid-cols-4">
            {['visibility', 'hearing', 'psychology', 'verified_user'].map((icon, index) => (
              <div key={icon} className="space-y-3">
                <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-white text-[#0a6a3c] shadow-sm">
                  <span className="material-symbols-outlined">{icon}</span>
                </div>
                <p className="font-semibold text-[#10202d]">{['Simple Icons', 'Voice Only Mode', 'Smart AI', 'No Scam Zone'][index]}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="security" className="mx-auto max-w-7xl px-5 py-8 lg:px-10">
          <div className="grid items-center gap-10 rounded-[2.2rem] bg-[#edf4ff] p-6 shadow-lg shadow-black/5 lg:grid-cols-[1fr_0.9fr] lg:p-10">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.26em] text-[#0a6a3c]">Security is our priority</p>
              <h2 className="mt-3 font-['Hanken_Grotesk'] text-3xl font-bold text-[#10202d] sm:text-4xl">Your money is safe with BMONI</h2>
              <p className="mt-5 max-w-xl text-base leading-8 text-[#51606e]">
                SabiSpend does not hold your money. We work with BMONI, a regulated partner, so savings stay locked away from scammers and remain under your control.
              </p>
              <ul className="mt-6 space-y-3 text-sm font-semibold text-[#10202d]">
                <li className="flex items-center gap-3"><span className="material-symbols-outlined text-[#25d366]">check</span>NDIC-insured wallets</li>
                <li className="flex items-center gap-3"><span className="material-symbols-outlined text-[#25d366]">check</span>24/7 scam message verification</li>
                <li className="flex items-center gap-3"><span className="material-symbols-outlined text-[#25d366]">check</span>Fingerprint or face unlock</li>
              </ul>
              <div className="mt-8 rounded-[1.4rem] bg-white p-5 shadow-sm ring-1 ring-[#d5dfec]">
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#0a6a3c]">Legal note</p>
                <p className="mt-3 text-sm leading-7 text-[#51606e]">
                  By using SabiSpend with BMONI, you agree to the BMONI Terms of Use and Privacy Policy that apply to your wallet and account activity. These terms govern how your data and funds are handled in the wallet flow, and they are part of the BMONI-linked experience inside this page.
                </p>
              </div>
              <a href={`https://wa.me/${whatsappNumber}`} target="_blank" rel="noopener noreferrer" className="mt-8 inline-flex items-center rounded-full bg-[#172533] px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-black/10 transition hover:bg-[#0f1821]">
                Read Security Policy
              </a>
            </div>
            <div className="rounded-[1.6rem] bg-white p-5 shadow-lg shadow-black/5">
              <div className="flex items-center justify-between border-b border-[#d5dfec] pb-4">
                <div className="flex items-center gap-3">
                  <div className="grid h-11 w-11 place-items-center rounded-full bg-[#0a6a3c]/10 text-[#0a6a3c]">
                    <span className="material-symbols-outlined">security</span>
                  </div>
                  <div>
                    <div className="font-bold">Scam Alert</div>
                    <div className="text-xs font-semibold text-[#51606e]">Forwarded by user</div>
                  </div>
                </div>
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#dc2626]">Scam detected</div>
              </div>
              <div className="mt-4 rounded-2xl border border-[#d5dfec] bg-[#fafcff] p-4 text-sm italic text-[#51606e]">
                "Congratulations! You won a big prize. Click here to claim it."
              </div>
              <div className="mt-4 rounded-2xl bg-[#fff0f0] p-4 text-sm text-[#dc2626]">
                This looks like a phishing attempt. Do not click the link.
              </div>
            </div>
          </div>
        </section>

        <section id="faq" className="mx-auto max-w-3xl px-5 py-20 lg:px-10">
          <div className="text-center">
            <p className="text-xs font-bold uppercase tracking-[0.26em] text-[#0a6a3c]">Common Questions</p>
            <h2 className="mt-3 font-['Hanken_Grotesk'] text-3xl font-bold text-[#10202d] sm:text-4xl">You ask, we answer</h2>
          </div>
          <div className="mt-10 space-y-4">
            {[
              ['Do I need to download an app?', 'No. SabiSpend lives on WhatsApp, so you can use it on any phone without extra downloads.'],
              ['Does it understand Pidgin?', 'Yes. It is designed for Pidgin, Yoruba, Hausa, and Igbo, with simple responses that stay easy to follow.'],
              ['Is my money safe?', 'Your funds stay in a secure partner wallet. SabiSpend helps you track and control them, but does not hold them directly.'],
              ['What is BMONI?', 'BMONI is the secure financial partner that powers the wallet layer behind the chat experience.']
            ].map(([q, a]) => (
              <details key={q} className="group rounded-2xl border border-[#d5dfec] bg-white px-5 py-4 shadow-sm">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold text-[#10202d]">
                  {q}
                  <span className="material-symbols-outlined transition group-open:rotate-180">expand_more</span>
                </summary>
                <p className="pt-4 text-sm leading-7 text-[#51606e]">{a}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="bg-[#0a6a3c] px-5 py-20 text-white">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="font-['Hanken_Grotesk'] text-3xl font-bold sm:text-4xl">Ready to Grow Your Money?</h2>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-white/85">Join thousands of Nigerian market women and artisans making smarter money moves today.</p>
            <a href={`https://wa.me/${whatsappNumber}`} target="_blank" rel="noopener noreferrer" className="mt-8 inline-flex items-center gap-3 rounded-full bg-white px-8 py-4 text-sm font-bold text-[#0a6a3c] shadow-lg shadow-black/10 transition hover:-translate-y-0.5">
              <span className="material-symbols-outlined">chat</span>
              Chat with SabiSpend
            </a>
            <p className="mt-4 text-xs font-semibold uppercase tracking-[0.22em] text-white/75">Free to use • Works on any phone with WhatsApp</p>
          </div>
        </section>
      </main>

      <footer className="bg-[#10202d] text-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-10 lg:flex-row lg:items-center lg:justify-between lg:px-10">
          <div className="max-w-sm">
            <div className="font-['Hanken_Grotesk'] text-xl font-bold">SabiSpend</div>
            <p className="mt-2 text-sm leading-7 text-white/70">AI money assistant for the real hustle. Built for Nigeria's traders, artisans, and everyday savers.</p>
          </div>
          <div className="flex flex-wrap gap-6 text-sm font-semibold text-white/70">
            <a href="#top" className="hover:text-white">Home</a>
            <a href="#faq" className="hover:text-white">FAQ</a>
            <a href="#features" className="hover:text-white">Features</a>
            <a href={`https://wa.me/${whatsappNumber}`} target="_blank" rel="noopener noreferrer" className="hover:text-white">WhatsApp</a>
          </div>
          <div className="text-sm font-semibold text-white/55">© 2026 SabiSpend. Built for Nigeria.</div>
        </div>
      </footer>
    </div>
  );
}
