Souhrn Problémů a Získaných Ponaučení v Projektu Sophia
1. Problémy s Prostředím a Závislostmi
Symptom: Aplikace se nespustí a hlásí ImportError: cannot import name 'BaseTool' from 'crewai.tools'.

Diagnóza: Nestabilní verze závislostí. Knihovna crewai se v průběhu času vyvíjela a měnila svou vnitřní strukturu, což vedlo k tomu, že importy, které fungovaly včera, dnes už nefungují. Problém nebyl v našem kódu, ale v prostředí, ve kterém běžel.

Poučení a Řešení:

Fixní Verze: Je absolutně klíčové mít v requirements.txt přesně "zamknuté" verze knihoven (např. crewai==0.35.8), aby se předešlo neočekávaným změnám.

Stabilní Prostředí pro Agenty: Tvůj objev s nastavením "Initial setup" pro Julese je nejlepší dlouhodobé řešení. Vytvoříme tak "zmrazený" snapshot prostředí, který zaručí, že kód bude vždy fungovat stejně.

2. Výzvy Paměťového Systému
Symptom 1: Sophia si nepamatuje nic z předchozích interakcí, přestože "proces snění" probíhá.

Diagnóza 1 (Slepota): Náš MemoryInspectionTool ukázal, že Dlouhodobá Paměť (LTM) je kompletně prázdná. Problém nebyl ve vybavování, ale v tom, že se nikdy nic neuložilo. MemoryAgent byl "mozek bez rukou" – neměl žádný nástroj pro fyzický zápis do databáze.

Poučení 1: Agent musí mít pro každou akci explicitní nástroj. Nespoléhat se na "implicitní" chování. Proto jsme vytvořili LtmWriteTool.

Symptom 2: LTM se plní, ale stále si nepamatuje konkrétní fakta z úkolů (např. o H2O). Místo toho obsahuje jen obecné fráze o důležitosti paměti.

Diagnóza 2 (Hluchota): MemoryAgent sice měl nástroj na zápis, ale nedostával žádné informace o tom, co se stalo v předchozí interakci s developer_agent. Byl izolovaný. Analyzoval jen svůj vlastní úkol ("zapiš vzpomínku") a zapsal si poznámku o zapisování vzpomínek.

Poučení 2: Je nutné zajistit přímý tok kontextu mezi různými agenty a procesy. Proto jsme v Architektuře V2.0 upravili main.py tak, aby výsledek jedné posádky byl předán jako vstup té následující.

3. Chyby v Autonomní Tvorbě Kódu (Její "Dětské Nemoci")
Tohle je nejfascinující část, kde jsme sledovali, jak se učí programovat.

Chyba 1 (Logická): Zapomněla, že třída nástroje musí dědit z BaseTool. Kód byl syntakticky správně, ale chyběl mu základní architektonický prvek.

Chyba 2 (Konzistence): Opravila dědičnost, ale použila import z langchain.tools místo crewai.tools, což bylo nekonzistentní se zbytkem projektu.

Chyba 3 (Jmenný Prostor): Vytvořila nástroj v novém souboru, ale snažila se ho importovat ze starého (custom_tools.py), protože nechápala, jak fungují Python moduly.

Chyba 4 (Syntaktická): Udělala jednoduchou chybu – zapomněla na uzavírací složenou závorku } v f-stringu.

Poučení: Sophia se učí jako člověk. Postupuje od základních syntaktických chyb, přes logické chyby, až po komplexnější architektonické problémy. Náš "Guardian Protocol" s automatickým git reset je naprosto klíčový, aby tyto chyby nebyly fatální.

4. Architektonické "Slepé Uličky"
Symptom: Sophia sice fungovala, ale její rozhodování nebylo skutečně autonomní.

Diagnóza: Spoléhali jsme se na "berličku" v podobě DecisionTool, který obsahoval pevně daná pravidla pro to, co je "znalost". Tím jsme jí brali tu nejdůležitější schopnost – samostatně usuzovat na základě své esence a kontextu.

Poučení: Skutečná autonomie nevznikne z pevných pravidel, ale z delegace a spolupráce. Proto je přechod na multi-agentní architekturu s Plánovačem, který úkoly rozděluje, tak zásadní.
