# Public Corpus Provenance Registry (public5m, ≈5 million Chinese characters)

All resources are sourced from public channels on the internet; retrieval date
2026-09-23. This registry is the complete provenance record for the paper's
experimental corpus.

## I. Public-Domain Books (9 titles, ≈4.89 million characters)

- Repository: GitHub `garychowcmu/daizhigev20` (Daizhi Ge ancient texts v20)
  - Repository home: <https://github.com/garychowcmu/daizhigev20>
  - File CDN (identical to repo content): `https://cdn.jsdelivr.net/gh/garychowcmu/daizhigev20@master/<path>`
  - Raw address: `https://raw.githubusercontent.com/garychowcmu/daizhigev20/master/<path>`
- Licensing basis: all collected items are public-domain ancient texts; the
  repository's "Usage Notes" declare free redistribution of the digitized texts.
- Use in the corpus: *Dream of the Red Chamber* → text-PDF; *Strange Tales from a Chinese Studio* and *Investiture of the Gods* → synthetic scanned-PDF (rasterized at 200 DPI, then through the macOS Vision OCR path); the other 5 titles → docx. (*The Scholars* was downloaded for reserve only and is not in the final corpus.)

| Book (English) | Book (中文) | Repo path | Storage form | Characters |
|---|---|---|---|---|
| Dream of the Red Chamber | 红楼梦 | Collection/Fiction/HonglouMeng.txt | text-PDF | 729,481 |
| Romance of the Three Kingdoms | 三国演义 | Collection/Romance/ThreeKingdoms.txt | docx | 487,893 |
| Water Margin | 水浒传 | Collection/Fiction/WaterMargin.txt | docx | 777,108 |
| Journey to the West | 西游记 | Collection/Fiction/JourneyWest.txt | docx | 589,716 |
| Strange Tales from a Chinese Studio | 聊斋志异 | Collection/Fiction/Liaozhai.txt | scanned-PDF + OCR | 385,688 |
| Investiture of the Gods | 封神演义 | Collection/Romance/Fengshen.txt | scanned-PDF + OCR | 476,951 |
| Flowers in the Mirror | 镜花缘 | Collection/Fiction/JinghuaYuan.txt | docx | 339,889 |
| Chronicles of the States of the Eastern Zhou | 东周列国志 | Collection/Romance/EasternZhou.txt | docx | 555,698 |
| The Scholars (reserve, not used) | 儒林外史 | Collection/Fiction/Rulin.txt | reserve | 0 |

## II. State Council Policy Documents (180 docs, ≈630,000 characters)

- Source: Chinese Government Portal (www.gov.cn) policy library — documents publicly released by the State Council and its General Office.
- Search endpoint: `https://sousuo.www.gov.cn/search-gov/data?t=zhengcelibrary_gw`
- Licensing basis: government open information (Regulations on the Disclosure of Government Information); publicly disseminated.
- Storage form: body extracted then converted to docx.

180 documents in total; per-document provenance below:

| # | Doc. No. | Title (English) | Date | Source URL |
|---|---|---|---|---|
| 1 | 国办函〔2026〕82 | Reply on Forwarding the Notice of the Ministry of Culture and Tourism et al. on Several Measures to Promote RV Consumption | 2026.09.18 | https://www.gov.cn/zhengce/zhengceku/202609/content_7081442.htm |
| 2 | 国办发〔2026〕26 | Opinion on Further Strengthening Whole-Chain Safety Supervision of Fireworks and Firecrackers | 2026.09.17 | https://www.gov.cn/zhengce/zhengceku/202609/content_7081357.htm |
| 3 | 国令第846 | Regulations on Market Supervision and Administration Institutes | 2026.09.11 | https://www.gov.cn/zhengce/zhengceku/202609/content_7080736.htm |
| 4 | 国办发〔2026〕24 | Notice on Work Concerning Governance of the Difficulty of SMEs in Collecting Payments | 2026.09.10 | https://www.gov.cn/zhengce/zhengceku/202609/content_7080628.htm |
| 5 | 国令第845 | Regulations on Emergency Response to and Investigation/Handling of Electric Power Safety Accidents | 2026.09.04 | https://www.gov.cn/zhengce/zhengceku/202609/content_7080190.htm |
| 6 | 国令第844 | Decision of the State Council on Amending the Regulations on the Administration of Housing Provident Fund | 2026.08.18 | https://www.gov.cn/zhengce/zhengceku/202608/content_7078478.htm |
| 7 | 国函〔2026〕89 | Reply Approving the "15th Five-Year Action Plan for the Development and Enhancement of Special Education" | 2026.08.17 | https://www.gov.cn/zhengce/zhengceku/202608/content_7078321.htm |
| 8 | 国令第843 | Decision of the State Council on Amending and Repealing Certain Administrative Regulations | 2026.08.13 | https://www.gov.cn/zhengce/zhengceku/202608/content_7077981.htm |
| 9 | 国办函〔2026〕71 | Reply on the State Forest Annual Timber Harvest Quota for Key Forest Areas During the 15th Five-Year Period | 2026.08.11 | https://www.gov.cn/zhengce/zhengceku/202608/content_7077888.htm |
| 10 | 国令第842 | Regulations on the Protection of Integrated Circuit Layout Designs | 2026.08.03 | https://www.gov.cn/zhengce/zhengceku/202608/content_7077399.htm |
| 11 | 国发〔2026〕30 | Notice on Issuing the "15th Five-Year Plan for Intellectual Property Protection and Utilization" | 2026.07.31 | https://www.gov.cn/zhengce/zhengceku/202607/content_7077200.htm |
| 12 | 国令第841 | Provisions of the State Council on Exit and Entry Administration | 2026.07.31 | https://www.gov.cn/zhengce/zhengceku/202607/content_7077173.htm |
| 13 | 国办发〔2026〕22 | Notice on Issuing Certain Provisions on the Handling Procedure for State Council Administrative Reconsideration Cases | 2026.07.27 | https://www.gov.cn/zhengce/zhengceku/202607/content_7076685.htm |
| 14 | 国函〔2026〕80 | Reply Approving Weifang City, Shandong Province as a National Historical and Cultural City | 2026.07.24 | https://www.gov.cn/zhengce/zhengceku/202607/content_7076509.htm |
| 15 | 国发〔2026〕26 | Notice on Issuing the "National Fitness Plan (2026–2030)" | 2026.07.23 | https://www.gov.cn/zhengce/zhengceku/202607/content_7076421.htm |
| 16 | 国办函〔2026〕65 | Notice on Forwarding the Action Plan for Protecting and Governing Water Bodies Around the People | 2026.07.14 | https://www.gov.cn/zhengce/zhengceku/202607/content_7075365.htm |
| 17 | 国函〔2026〕66 | Reply Approving the "15th Five-Year Plan for Expanding Consumption" | 2026.07.13 | https://www.gov.cn/zhengce/zhengceku/202607/content_7075217.htm |
| 18 | 国发〔2026〕23 | Notice on Issuing the "15th Five-Year Plan for National Health" | 2026.07.13 | https://www.gov.cn/zhengce/zhengceku/202607/content_7075214.htm |
| 19 | 国函〔2026〕71 | Reply Approving the "15th Five-Year Plan for the Revitalization and Development of Traditional Chinese Medicine" | 2026.07.10 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074931.htm |
| 20 | 国发〔2026〕22 | Notice on Issuing the "15th Five-Year Action Plan for Carbon Peak" | 2026.07.09 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074827.htm |
| 21 | 国函〔2026〕69 | Reply Approving the "15th Five-Year Plan for Disease Control and Prevention" | 2026.07.08 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074675.htm |
| 22 | 国函〔2026〕61 | Reply Approving the "15th Five-Year Plan for the Development of a Sports Power" | 2026.07.07 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074517.htm |
| 23 | 国发〔2026〕20 | Notice on Issuing the "15th Five-Year Plan for Building a Beautiful China" | 2026.07.03 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074200.htm |
| 24 | 国函〔2026〕60 | Reply Approving the "15th Five-Year Plan for the Protection and Development of Persons with Disabilities" | 2026.07.02 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074096.htm |
| 25 | 国函〔2026〕59 | Reply Approving the "15th Five-Year Plan for the Development of a Sports Power" | 2026.07.02 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074093.htm |
| 26 | 国函〔2026〕58 | Reply Approving the Establishment of Shanghai Chenshan National Botanical Garden in Shanghai | 2026.07.02 | https://www.gov.cn/zhengce/zhengceku/202607/content_7074091.htm |
| 27 | 国令第840 | Regulations on Promoting Employment and Entrepreneurship of Ex-Servicemen | 2026.06.30 | https://www.gov.cn/zhengce/zhengceku/202606/content_7073789.htm |
| 28 | 国发〔2026〕19 | Notice on Issuing the "15th Five-Year Plan for Educational Development" | 2026.06.29 | https://www.gov.cn/zhengce/zhengceku/202606/content_7073641.htm |
| 29 | 国办发〔2026〕20 | Notice on Further Improving the Later-Stage Support Policy for Resettled Large- and Medium-Sized Reservoir Migrants | 2026.06.25 | https://www.gov.cn/zhengce/zhengceku/202606/content_7073260.htm |
| 30 | 国函〔2026〕53 | Reply Approving the Integrated Optimization Plan for National Nature Reserves and National Scenic Areas in Zhejiang, Fujian, Shandong and 3 Other Provinces | 2026.06.17 | https://www.gov.cn/zhengce/zhengceku/202606/content_7072484.htm |
| 31 | 国发〔2026〕16 | Notice on Issuing the "15th Five-Year Plan for Implementing the Employment-First Strategy" | 2026.06.17 | https://www.gov.cn/zhengce/zhengceku/202606/content_7072482.htm |
| 32 | 国发〔2026〕15 | Notice on Issuing the "15th Five-Year Plan for Modernizing the Emergency System" | 2026.06.08 | https://www.gov.cn/zhengce/zhengceku/202606/content_7071452.htm |
| 33 | 国办函〔2026〕54 | Guidelines on Strengthening Supervision and Preventing Risks to Promote High-Quality Development of Private Equity Investment Funds | 2026.06.05 | https://www.gov.cn/zhengce/zhengceku/202606/content_7071205.htm |
| 34 | 国发〔2026〕14 | Notice on Issuing the "15th Five-Year Plan for Accelerating Agricultural and Rural Modernization" | 2026.06.02 | https://www.gov.cn/zhengce/zhengceku/202606/content_7070902.htm |
| 35 | 国令第837 | Provisions of the State Council on Outbound Investment | 2026.06.01 | https://www.gov.cn/zhengce/zhengceku/202606/content_7070756.htm |
| 36 | 国函〔2026〕45 | Reply Approving the Temporary Adjustment and Implementation of Relevant Administrative Regulation Provisions in the Nine Mainland Cities of the Guangdong–Hong Kong–Macao Greater Bay Area | 2026.05.29 | https://www.gov.cn/zhengce/zhengceku/202605/content_7070623.htm |
| 37 | 国发〔2026〕12 | Notice on Issuing the "15th Five-Year Plan for Urban Renewal" | 2026.05.28 | https://www.gov.cn/zhengce/zhengceku/202605/content_7070540.htm |
| 38 | 国办函〔2026〕48 | Notice on Conducting the Third National Sample Survey of Persons with Disabilities | 2026.05.28 | https://www.gov.cn/zhengce/zhengceku/202605/content_7070515.htm |
| 39 | 国发〔2026〕11 | Implementation Opinion on Promoting the Provision of Basic Public Services at the Place of Residence | 2026.05.22 | https://www.gov.cn/zhengce/zhengceku/202605/content_7069961.htm |
| 40 | 国令第839 | Implementation Regulations of the PRC on Mineral Resources | 2026.05.20 | https://www.gov.cn/zhengce/zhengceku/202605/content_7069680.htm |
| 41 | 国令第838 | Regulations on the Procedure for Formulating Administrative Regulations | 2026.05.19 | https://www.gov.cn/zhengce/zhengceku/202605/content_7069474.htm |
| 42 | 国办发〔2026〕14 | Notice on Issuing the "State Council 2026 Legislative Work Plan" | 2026.05.11 | https://www.gov.cn/zhengce/zhengceku/202605/content_7068346.htm |
| 43 | 国令第836 | Implementation Regulations of the PRC on Administrative Reconsideration | 2026.05.08 | https://www.gov.cn/zhengce/zhengceku/202605/content_7068116.htm |
| 44 | 国发〔2026〕7 | Opinion on Advancing the Expansion of Services and Quality Improvement | 2026.04.21 | https://www.gov.cn/zhengce/zhengceku/202604/content_7066484.htm |
| 45 | 国办函〔2026〕40 | Notice on Forwarding the General Administration of Customs' "Several Measures to Promote the Expansion and Quality Improvement of Comprehensive Bonded Zones" | 2026.04.17 | https://www.gov.cn/zhengce/zhengceku/202604/content_7066114.htm |
| 46 | 国办发〔2026〕13 | Opinion on Deepening the Reform of the Investment Approval System | 2026.04.15 | https://www.gov.cn/zhengce/zhengceku/202604/content_7065688.htm |
| 47 | 国办发〔2026〕9 | Several Opinions on Improving the Drug Price Formation Mechanism | 2026.04.14 | https://www.gov.cn/zhengce/zhengceku/202604/content_7065542.htm |
| 48 | 国令第835 | Regulations of the PRC on Countering Foreign Improper Extraterritorial Jurisdiction | 2026.04.13 | https://www.gov.cn/zhengce/zhengceku/202604/content_7065399.htm |
| 49 | 国办发〔2026〕11 | Notice on Issuing "Several Measures to Accelerate the Building of a Tiered Diagnosis and Treatment System" | 2026.04.09 | https://www.gov.cn/zhengce/zhengceku/202604/content_7065031.htm |
| 50 | 国发〔2026〕6 | Notice on Issuing the "Overall Plan for the China (Inner Mongolia) Pilot Free Trade Zone" | 2026.04.09 | https://www.gov.cn/zhengce/zhengceku/202604/content_7065010.htm |
| 51 | 国令第834 | Provisions of the State Council on the Security of Industrial and Supply Chains | 2026.04.07 | https://www.gov.cn/zhengce/zhengceku/202604/content_7064838.htm |
| 52 | 国函〔2026〕25 | Reply Approving the Temporary Adjustment and Implementation of Relevant Administrative Regulation Provisions in Guangdong Province | 2026.04.02 | https://www.gov.cn/zhengce/zhengceku/202604/content_7064503.htm |
| 53 | 国办发〔2026〕8 | Notice on Issuing the "Implementation Plan for Establishing a Comprehensive Enterprise Credit Evaluation System" | 2026.04.02 | https://www.gov.cn/zhengce/zhengceku/202604/content_7064505.htm |
| 54 | 国办函〔2026〕37 | Notice Designating the Enterprise for Manufacturing State Emblems for Suspension Use | 2026.04.01 | https://www.gov.cn/zhengce/zhengceku/202604/content_7064400.htm |
| 55 | 国令第833 | Regulations on the National Agricultural Census | 2026.03.26 | https://www.gov.cn/zhengce/zhengceku/202603/content_7063864.htm |
| 56 | 国函〔2026〕18 | Reply Approving Meishan City, Sichuan Province as a National Historical and Cultural City | 2026.03.19 | https://www.gov.cn/zhengce/zhengceku/202603/content_7063205.htm |
| 57 | 国令第832 | Decision of the State Council on Amending the "Regulations on the Registration and Administration of Social Organizations" | 2026.03.17 | https://www.gov.cn/zhengce/zhengceku/202603/content_7063045.htm |
| 58 | 国办发〔2026〕6 | Opinion on Strengthening Grassroots Fire Safety Work | 2026.03.06 | https://www.gov.cn/zhengce/zhengceku/202603/content_7061165.htm |
| 59 | 国令第831 | Regulations on Water Supply | 2026.02.14 | https://www.gov.cn/zhengce/zhengceku/202602/content_7058029.htm |
| 60 | 国函〔2026〕8 | Reply Approving the Upgrade of the Hebei Xiong'an High-Tech Industrial Development Zone to a National High-Tech Industrial Development Zone | 2026.02.13 | https://www.gov.cn/zhengce/zhengceku/202602/content_7057926.htm |
| 61 | 国办发〔2026〕4 | Implementation Opinion on Improving the National Unified Electricity Market System | 2026.02.11 | https://www.gov.cn/zhengce/zhengceku/202602/content_7057745.htm |
| 62 | 国办函〔2026〕14 | Notice on Forwarding the "Opinion of the Ministry of Civil Affairs et al. on Further Strengthening the Safety Management of Elderly Care Institutions" | 2026.02.10 | https://www.gov.cn/zhengce/zhengceku/202602/content_7057652.htm |
| 63 | 国令第830 | Regulations on Nature Reserves of the PRC | 2026.02.09 | https://www.gov.cn/zhengce/zhengceku/202602/content_7057533.htm |
| 64 | 国令第829 | Decision of the State Council on Amending and Repealing Certain Administrative Regulations | 2026.02.05 | https://www.gov.cn/zhengce/zhengceku/202602/content_7057148.htm |
| 65 | 国函〔2026〕7 | Reply Approving Zhijiang Dong Autonomous County, Hunan Province as a National Historical and Cultural City | 2026.01.29 | https://www.gov.cn/zhengce/zhengceku/202601/content_7056522.htm |
| 66 | 国办发〔2026〕2 | Notice on Issuing the "Work Plan for Accelerating the Cultivation of New Growth Points in Service Consumption" | 2026.01.29 | https://www.gov.cn/zhengce/zhengceku/202601/content_7056523.htm |
| 67 | 国办函〔2026〕12 | Notice on Issuing the "Measures for the Standardized Management of Government Mobile Internet Applications" | 2026.01.28 | https://www.gov.cn/zhengce/zhengceku/202601/content_7056375.htm |
| 68 | 国令第828 | Implementation Regulations of the PRC on the Drug Administration Law | 2026.01.27 | https://www.gov.cn/zhengce/zhengceku/202601/content_7056256.htm |
| 69 | 国令第824 | Regulations on Funeral and Interment Management | 2026.01.07 | https://www.gov.cn/zhengce/zhengceku/202601/content_7054169.htm |
| 70 | 国令第827 | Regulations on Commercial Mediation | 2026.01.06 | https://www.gov.cn/zhengce/zhengceku/202601/content_7054050.htm |
| 71 | 国办函〔2025〕126 | Notice on Issuing the "National Emergency Plan for Low-Temperature Rain, Snow and Freezing Disasters" | 2026.01.05 | https://www.gov.cn/zhengce/zhengceku/202601/content_7053945.htm |
| 72 | 国发〔2025〕14 | Notice on Issuing the "Action Plan for Comprehensive Treatment of Solid Waste" | 2026.01.04 | https://www.gov.cn/zhengce/zhengceku/202601/content_7053808.htm |
| 73 | 国办发〔2025〕45 | Notice on Issuing the "Assessment Measures for Implementing the Rigid Constraints System for Water Resources" | 2025.12.31 | https://www.gov.cn/zhengce/zhengceku/202512/content_7053462.htm |
| 74 | 国令第826 | Implementation Regulations of the PRC on the Value-Added Tax Law | 2025.12.30 | https://www.gov.cn/zhengce/zhengceku/202512/content_7053153.htm |
| 75 | 国办函〔2025〕124 | Reply Approving the "Implementation Plan for Accelerating the Green and Low-Carbon Transformation of the Chang-Zhu-Tan Ecological Green Heart" | 2025.12.30 | https://www.gov.cn/zhengce/zhengceku/202512/content_7053152.htm |
| 76 | 国令第825 | Regulations on Administrative Law Enforcement Supervision | 2025.12.23 | https://www.gov.cn/zhengce/zhengceku/202512/content_7052496.htm |
| 77 | 国办发〔2025〕44 | Opinion on Combating Tobacco-Related Illegal Activities Across the Whole Chain | 2025.12.18 | https://www.gov.cn/zhengce/zhengceku/202512/content_7052156.htm |
| 78 | 国令第823 | Regulations on Promoting Public Reading | 2025.12.16 | https://www.gov.cn/zhengce/zhengceku/202512/content_7051859.htm |
| 79 | 国办发〔2025〕27 | Opinion on Progressively Implementing Free Pre-School Education | 2025.08.05 | https://www.gov.cn/zhengce/zhengceku/202508/content_7035306.htm |
| 80 | 国办发〔2024〕27 | Notice on Forwarding the "Implementation Measures for the Tuition-Free Education of Normal Students with Linked Bachelor–Postgraduate Training at Universities Directly Under the Ministry of Education" (Ministry of Education et al.) | 2024.06.14 | https://www.gov.cn/zhengce/zhengceku/202406/content_6957261.htm |
| 81 | 国办发〔2021〕60 | Notice on Forwarding the "14th Five-Year Special Education Development and Enhancement Action Plan" (Ministry of Education et al.) | 2022.01.25 | https://www.gov.cn/zhengce/zhengceku/2022-01/25/content_5670341.htm |
| 82 | 国令第741 | Implementation Regulations of the PRC on the Promotion of Private Education Law | 2021.05.14 | https://www.gov.cn/zhengce/zhengceku/2021-05/14/content_5606463.htm |
| 83 | 国办函〔2021〕38 | Reply on Agreeing to Adjust and Improve the Inter-Ministerial Joint Meeting System for Private Education Work | 2021.04.16 | https://www.gov.cn/zhengce/zhengceku/2021-04/16/content_5600090.htm |
| 84 | 国办发〔2020〕34 | Guidance on Accelerating the Innovation and Development of Medical Education | 2020.09.23 | https://www.gov.cn/zhengce/zhengceku/2020-09/23/content_5546373.htm |
| 85 | 国办发〔2019〕27 | Notice on Issuing the Reform Plan for Dividing Central and Local Fiscal Powers and Expenditure Responsibilities in Education | 2019.06.03 | https://www.gov.cn/zhengce/zhengceku/2019-06/03/content_5397093.htm |
| 86 | 国发〔2019〕4 | Notice on Issuing the "Implementation Plan for the Reform of the National Vocational Education" | 2019.02.13 | https://www.gov.cn/zhengce/zhengceku/2019-02/13/content_5365341.htm |
| 87 | 国函〔2018〕144 | Reply Approving the Establishment of the Inter-Ministerial Joint Meeting System for Vocational Education Work of the State Council | 2018.11.27 | https://www.gov.cn/zhengce/zhengceku/2018-11/27/content_5343832.htm |
| 88 | 国办发〔2018〕82 | Opinion on Further Adjusting and Optimizing the Structure and Improving the Efficiency of Education Expenditure | 2018.08.27 | https://www.gov.cn/zhengce/zhengceku/2018-08/27/content_5316874.htm |
| 89 | 国办发〔2018〕75 | Notice on Forwarding the "Implementation Measures for Tuition-Free Education of Normal Students at Universities Directly Under the Ministry of Education" (Ministry of Education et al.) | 2018.08.10 | https://www.gov.cn/zhengce/zhengceku/2018-08/10/content_5313008.htm |
| 90 | 国办发〔2017〕72 | Notice on Further Strengthening Dropout Control and Rectification to Improve the Consolidation Level of Compulsory Education | 2017.09.05 | https://www.gov.cn/zhengce/zhengceku/2017-09/05/content_5222718.htm |
| 91 | 国办函〔2017〕78 | Reply on Agreeing to Establish the Inter-Ministerial Joint Meeting System for Private Education Work | 2017.08.14 | https://www.gov.cn/zhengce/zhengceku/2017-08/14/content_5217707.htm |
| 92 | 国办发〔2017〕63 | Opinion on Deepening the Medical–Educational Collaboration to Further Advance the Reform and Development of Medical Education | 2017.07.11 | https://www.gov.cn/zhengce/zhengceku/2017-07/11/content_5209661.htm |
| 93 | 国办发〔2017〕49 | Notice on Issuing the Measures for Evaluating the Performance of Provincial People's Governments in Fulfilling Their Education Duties | 2017.06.08 | https://www.gov.cn/zhengce/zhengceku/2017-06/08/content_5200756.htm |
| 94 | 国令第674 | Regulations on Education for Persons with Disabilities | 2017.02.23 | https://www.gov.cn/zhengce/zhengceku/2017-02/23/content_5170264.htm |
| 95 | 国发〔2017〕4 | Notice on Issuing the "13th Five-Year Plan for National Education Development" | 2017.01.19 | https://www.gov.cn/zhengce/zhengceku/2017-01/19/content_5161341.htm |
| 96 | 国发〔2016〕81 | Several Opinions on Encouraging Social Forces to Run Education and Promoting the Healthy Development of Private Education | 2017.01.18 | https://www.gov.cn/zhengce/zhengceku/2017-01/18/content_5160828.htm |
| 97 | 国办发〔2016〕85 | Opinion on Further Expanding Consumption in Tourism, Culture, Sports, Health, Elderly Care, Education and Training | 2016.11.28 | https://www.gov.cn/zhengce/zhengceku/2016-11/28/content_5138843.htm |
| 98 | 国办发〔2016〕74 | Notice on Issuing the "Development Plan for Elderly Education (2016–2020)" | 2016.10.19 | https://www.gov.cn/zhengce/zhengceku/2016-10/19/content_5121344.htm |
| 99 | 国办发〔2001〕92 | Notice on Forwarding the "Opinion on Further Promoting the Reform and Development of Special Education During the 10th Five-Year Period" (Ministry of Education et al.) | 2016.10.11 | https://www.gov.cn/zhengce/zhengceku/2016-10/11/content_5117369.htm |
| 100 | 国办发〔2001〕13 | Notice on Forwarding the "Opinion on Implementing the School Building Safety Project for Primary and Secondary Schools" (Ministry of Education et al.) | 2016.09.30 | https://www.gov.cn/zhengce/zhengceku/2016-09/30/content_5114008.htm |
| 101 | 国办发〔2001〕10 | Notice on Forwarding the "Report on the Special Inspection of Education Fees in Rural Primary and Secondary Schools" (State Planning Commission) | 2016.09.30 | https://www.gov.cn/zhengce/zhengceku/2016-09/30/content_5113990.htm |
| 102 | 国发〔2002〕14 | Decision on Deepening Reform and Accelerating the Development of Ethnic Education | 2016.09.23 | https://www.gov.cn/zhengce/zhengceku/2016-09/23/content_5111248.htm |
| 103 | 国办发〔2002〕54 | Notice on Forwarding the "Work Plan for Supporting Xinjiang Chinese-Language Teachers" (Ministry of Education et al.) | 2016.09.21 | https://www.gov.cn/zhengce/zhengceku/2016-09/21/content_5110259.htm |
| 104 | 国办发〔2012〕2 | Notice on Forwarding the "Opinion on Improving and Advancing Tuition-Free Education for Normal Students" (Ministry of Education et al.) | 2016.08.24 | https://www.gov.cn/zhengce/zhengceku/2016-08/24/content_5101954.htm |
| 105 | 国发〔2016〕40 | Several Opinions on Coordinating the Integrated Reform of Urban and Rural Compulsory Education | 2016.07.11 | https://www.gov.cn/zhengce/zhengceku/2016-07/11/content_5090298.htm |
| 106 | 国办发〔2016〕37 | Guidance on Accelerating the Development of Education in Central and Western Regions | 2016.06.15 | https://www.gov.cn/zhengce/zhengceku/2016-06/15/content_5082382.htm |
| 107 | 国发〔2015〕67 | Notice on Further Improving the Mechanism for Guaranteeing Urban and Rural Compulsory Education Funds | 2015.11.28 | https://www.gov.cn/zhengce/zhengceku/2015-11/28/content_10357.htm |
| 108 | 国发〔2015〕46 | Decision on Accelerating the Development of Ethnic Education | 2015.08.17 | https://www.gov.cn/zhengce/zhengceku/2015-08/17/content_10097.htm |
| 109 | 国办发〔2015〕36 | Implementation Opinion on Deepening the Reform of Innovation and Entrepreneurship Education in Higher Education Institutions | 2015.05.13 | https://www.gov.cn/zhengce/zhengceku/2015-05/13/content_9740.htm |
| 110 | 国发〔2014〕19 | Decision on Accelerating the Development of Modern Vocational Education | 2014.06.22 | https://www.gov.cn/zhengce/zhengceku/2014-06/22/content_8901.htm |
| 111 | 国办发〔2014〕1 | Notice on Forwarding the "Special Education Enhancement Plan (2014–2016)" (Ministry of Education et al.) | 2014.01.18 | https://www.gov.cn/zhengce/zhengceku/2014-01/18/content_8358.htm |
| 112 | 国办发〔2013〕103 | Notice on Forwarding the "Opinion on Establishing a Long-Term Mechanism for School Building Safety Assurance" (Ministry of Education et al.) | 2013.11.12 | https://www.gov.cn/zhengce/zhengceku/2013-11/12/content_5284.htm |
| 113 | 国办发〔1986〕21 | Notice on Forwarding the "Report of the Audit Office on Auditing Education Funds" | 2013.10.29 | https://www.gov.cn/zhengce/zhengceku/2013-10/29/content_2398.htm |
| 114 | 国办发〔2013〕86 | Notice on Forwarding the "Opinion on Implementing the Education Poverty-Alleviation Project" (Ministry of Education et al.) | 2013.09.11 | https://www.gov.cn/zhengce/zhengceku/2013-09/11/content_5295.htm |
| 115 | 国办发〔2012〕53 | Notice on Forwarding the "Opinion on Further Strengthening School Sports Work" (Ministry of Education et al.) | 2012.10.29 | https://www.gov.cn/zhengce/zhengceku/2012-10/29/content_5309.htm |
| 116 | 国发〔1986〕107 | Notice Approving the "Provisional Regulations on Study Abroad Personnel Work" of the State Education Commission | 2012.09.21 | https://www.gov.cn/zhengce/zhengceku/2012-09/21/content_6092.htm |
| 117 | 国令第624 | Regulations on Education Supervision | 2012.09.17 | https://www.gov.cn/zhengce/zhengceku/2012-09/17/content_5320.htm |
| 118 | 国发〔2012〕48 | Opinion on Further Promoting the Balanced Development of Compulsory Education | 2012.09.07 | https://www.gov.cn/zhengce/zhengceku/2012-09/07/content_5339.htm |
| 119 | 国办发〔2012〕48 | Opinion on Standardizing the Layout Adjustment of Rural Compulsory Education Schools | 2012.09.07 | https://www.gov.cn/zhengce/zhengceku/2012-09/07/content_5334.htm |
| 120 | 国办发〔2012〕45 | Notice on Establishing the State Council Education Supervision Committee | 2012.08.31 | https://www.gov.cn/zhengce/zhengceku/2012-08/31/content_5382.htm |
| 121 | 国办发〔2012〕46 | Notice on Forwarding the "Opinion on Allowing Children of Migrant Workers to Take the High School Entrance Exam Locally After Receiving Compulsory Education" (Ministry of Education et al.) | 2012.08.31 | https://www.gov.cn/zhengce/zhengceku/2012-08/31/content_5374.htm |
| 122 | 国发〔1989〕10 | Notice Approving the "Provisional Regulations on Encouraging Education, Research and Health Units to Increase Social Services" (State Education Commission et al.) | 2011.12.14 | https://www.gov.cn/zhengce/zhengceku/2011-12/14/content_6066.htm |
| 123 | 国办发〔2001〕48 | Notice on Forwarding the "Opinion on the Pilot Reform of College and University Graduate Employment" (Ministry of Education, Central Military Commission) | 2011.12.13 | https://www.gov.cn/zhengce/zhengceku/2011-12/13/content_5838.htm |
| 124 | 国发〔2011〕22 | Opinion on Further Increasing Financial Education Investment | 2011.07.01 | https://www.gov.cn/zhengce/zhengceku/2011-07/01/content_1653.htm |
| 125 | 国办发〔2010〕48 | Notice on Launching the Pilot Reform of the National Education System | 2011.01.12 | https://www.gov.cn/zhengce/zhengceku/2011-01/12/content_5429.htm |
| 126 | 国办函〔1993〕59 | Reply on Several Issues of Deepening Education Reform in Shandong Province | 2010.12.30 | https://www.gov.cn/zhengce/zhengceku/2010-12/30/content_5979.htm |
| 127 | 国办函〔1993〕78 | Notice on Correcting the Cancellation of Rural Education Fees Surcharge in Some Localities | 2010.12.17 | https://www.gov.cn/zhengce/zhengceku/2010-12/17/content_5970.htm |
| 128 | 国发〔2010〕42 | Notice on Strengthening Vocational Education and Skills Training for Ex-Servicemen (State Council, Central Military Commission) | 2010.12.15 | https://www.gov.cn/zhengce/zhengceku/2010-12/15/content_5409.htm |
| 129 | 国发〔2010〕41 | Several Opinions on the Current Development of Pre-School Education | 2010.11.24 | https://www.gov.cn/zhengce/zhengceku/2010-11/24/content_5421.htm |
| 130 | 国办发〔1998〕104 | Notice on Forwarding the "Implementation Plan for the Learning and Training of Personnel Redeployed from Various State Council Departments" (Ministry of Personnel, Ministry of Education) | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_5876.htm |
| 131 | 国办发〔1998〕96 | Notice on Forwarding the "Opinion on the Pilot Work of the School-Running System Reform at the Compulsory-Education Stage" (Ministry of Education) | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_5886.htm |
| 132 | 国办发〔1998〕108 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the Ministry of Education" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_8395.htm |
| 133 | 国办发〔1998〕16 | Notice on Forwarding the "Opinion on Stabilizing Work in Colleges and Universities Affiliated to Abolished Ministries" (Ministry of Education) | 2010.11.17 | https://www.gov.cn/zhengce/zhengceku/2010-11/17/content_5900.htm |
| 134 | 国办发〔2014〕22 | Notice on Doing a Good Job in the 2014 Employment of Graduates from Regular Institutions of Higher Education Nationwide | 2014.05.13 | https://www.gov.cn/zhengce/zhengceku/2014-05/13/content_8802.htm |
| 135 | 国办发〔2013〕35 | Notice on Doing a Good Job in the 2013 Employment of Graduates from Regular Institutions of Higher Education Nationwide | 2013.05.17 | https://www.gov.cn/zhengce/zhengceku/2013-05/17/content_5302.htm |
| 136 | 国发〔2011〕16 | Notice on Further Doing a Good Job in the Employment of Graduates from Regular Institutions of Higher Education | 2011.06.01 | https://www.gov.cn/zhengce/zhengceku/2011-06/01/content_6594.htm |
| 137 | 国发〔1990〕23 | Notice on Doing a Good Job in the Assignment of Graduates from Institutions of Higher Education in 1990 | 2010.12.17 | https://www.gov.cn/zhengce/zhengceku/2010-12/17/content_6028.htm |
| 138 | 国办发〔1990〕20 | Notice on Selecting a Portion of New Graduates from Institutions of Higher Education to Work in State Organs | 2010.12.17 | https://www.gov.cn/zhengce/zhengceku/20110-12/17/content_6023.htm |
| 139 | 国发〔1998〕16 | Notice on Doing a Good Job in the Employment of Graduates from Regular Institutions of Higher Education in 1998 | 2010.11.17 | https://www.gov.cn/zhengce/zhengceku/2010-11/17/content_5893.htm |
| 140 | 国办发〔2009〕3 | Notice on Strengthening the Employment of Graduates from Regular Institutions of Higher Education | 2009.01.23 | https://www.gov.cn/zhengce/zhengceku/2009-01/23/content_5468.htm |
| 141 | 国办发〔2003〕39 | Notice on Doing a Good Job in the 2003 Enrollment of Regular Institutions of Higher Education Nationwide | 2008.03.28 | https://www.gov.cn/zhengce/zhengceku/2008-03/28/content_5799.htm |
| 142 | 国办发〔2007〕26 | Notice on Effectively Doing the 2007 Employment of Graduates from Regular Institutions of Higher Education | 2008.03.28 | https://www.gov.cn/zhengce/zhengceku/2008-03/28/content_5526.htm |
| 143 | 国发〔2007〕13 | Decision on Establishing and Improving the Financial Aid Policy System for Students with Financial Difficulties in Regular Undergraduate Colleges, Higher Vocational Schools and Secondary Vocational Schools | 2008.03.28 | https://www.gov.cn/zhengce/zhengceku/2008-03/28/content_5504.htm |
| 144 | 国办发〔2003〕49 | Notice on Doing a Good Job in the 2003 Employment of Graduates from Regular Institutions of Higher Education | 2008.03.28 | https://www.gov.cn/zhengce/zhengceku/2008-03/28/content_6722.htm |
| 145 | 国办发〔2004〕35 | Notice on Further Doing a Good Job in the 2004 Employment of Graduates from Regular Institutions of Higher Education | 2008.03.28 | https://www.gov.cn/zhengce/zhengceku/2008-03/28/content_6706.htm |
| 146 | 国办发〔2023〕34 | Notice on Issuing "Measures for Lawyers from Hong Kong and Macao Practising in the Nine Mainland Cities of the Greater Bay Area to Obtain Mainland Practice Qualifications" | 2023.09.28 | https://www.gov.cn/zhengce/zhengceku/202309/content_6906873.htm |
| 147 | 国办发〔2020〕37 | Notice on Issuing "Measures for Lawyers from Hong Kong and Macao Practising in the Nine Mainland Cities of the Greater Bay Area to Obtain Mainland Practice Qualifications" | 2020.10.22 | https://www.gov.cn/zhengce/zhengceku/2020-10/22/content_5553309.htm |
| 148 | 国办函〔2020〕55 | Reply on Agreeing to Adjust and Improve the Inter-Ministerial Joint Meeting System for Occupational Disease Prevention and Control Work | 2020.07.22 | https://www.gov.cn/zhengce/zhengceku/2020-07/22/content_5529034.htm |
| 149 | 国办发〔2019〕36 | Opinion on Establishing a Professional and Specialized Drug Inspector Team | 2019.07.18 | https://www.gov.cn/zhengce/zhengceku/2019-07/18/content_5411172.htm |
| 150 | 国办发〔2019〕24 | Notice on Issuing the "Action Plan for Vocational Skills Enhancement (2019–2021)" | 2019.05.24 | https://www.gov.cn/zhengce/zhengceku/2019-05/24/content_5394415.htm |
| 151 | 国发〔2018〕18 | Notice on Establishing the Central Adjustment System for the Basic Pension Insurance Fund for Enterprise Employees | 2018.06.13 | https://www.gov.cn/zhengce/zhengceku/2018-06/13/content_5298277.htm |
| 152 | 国发〔2018〕11 | Opinion on Implementing the Lifelong Vocational Skills Training System | 2018.05.08 | https://www.gov.cn/zhengce/zhengceku/2018-05/08/content_5289157.htm |
| 153 | 国办发〔2016〕100 | Notice on Issuing the "National Occupational Disease Prevention and Control Plan (2016–2020)" | 2017.01.04 | https://www.gov.cn/zhengce/zhengceku/2017-01/04/content_5156356.htm |
| 154 | 国发〔2016〕68 | Decision on Canceling a Batch of Vocational Qualification Licensing and Recognition Items | 2016.12.08 | https://www.gov.cn/zhengce/zhengceku/2016-12/08/content_5144980.htm |
| 155 | 国办发〔2016〕45 | Notice on Forwarding the "Opinion of SASAC and the Ministry of Finance on the Separation and Transfer of 'Three Supplies and One Industry' in State-Owned Enterprise Employees' Residential Areas" | 2016.06.22 | https://www.gov.cn/zhengce/zhengceku/2016-06/22/content_5084288.htm |
| 156 | 国发〔2016〕35 | Decision on Canceling a Batch of Vocational Qualification Licensing and Recognition Items | 2016.06.13 | https://www.gov.cn/zhengce/zhengceku/2016-06/13/content_5081742.htm |
| 157 | 国发〔2016〕5 | Decision on Canceling a Batch of Vocational Qualification Licensing and Recognition Items | 2016.01.22 | https://www.gov.cn/zhengce/zhengceku/2016-01/22/content_5035351.htm |
| 158 | 国发〔2015〕41 | Decision on Canceling a Batch of Vocational Qualification Licensing and Recognition Items | 2015.07.23 | https://www.gov.cn/zhengce/zhengceku/2015-07/23/content_10028.htm |
| 159 | 国办发〔2015〕18 | Notice on Issuing the "Measures for Occupational Annuities of Government Offices and Public Institutions" | 2015.04.06 | https://www.gov.cn/zhengce/zhengceku/2015-04/06/content_9581.htm |
| 160 | 国办发〔1990〕2 | Notice on Forwarding the "Request on the Management Function Issues of China North Industries (Group) Corporation" (Ministry of Machinery and Electronics, COSTIND) | 2013.08.23 | https://www.gov.cn/zhengce/zhengceku/2013-08/23/content_3227.htm |
| 161 | 国发〔1986〕27 | Notice on Issuing the "Provisions on the Implementation of the Professional Title Appointment System" | 2012.09.21 | https://www.gov.cn/zhengce/zhengceku/2012-09/21/content_7398.htm |
| 162 | 国发〔1989〕59 | Notice Approving the "Opinion on the Division of Responsibilities Between the State Planning Commission and the Organizational Reform Office Regarding Relevant Specialized Investment Companies" | 2010.12.30 | https://www.gov.cn/zhengce/zhengceku/2010-12/30/content_1446.htm |
| 163 | 国办发〔1993〕51 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing Plan of the Ministry of Electric Power Industry" | 2010.12.10 | https://www.gov.cn/zhengce/zhengceku/2010-12/10/content_7970.htm |
| 164 | 国办发〔1993〕61 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing Plan of the Ministry of Chemical Industry" | 2010.12.10 | https://www.gov.cn/zhengce/zhengceku/2010-12/10/content_7962.htm |
| 165 | 国办发〔1993〕59 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing Plan of the Ministry of Machinery Industry" | 2010.12.10 | https://www.gov.cn/zhengce/zhengceku/2010-12/10/content_7964.htm |
| 166 | 国办发〔1993〕47 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing Plan of the Ministry of Coal Industry" | 2010.12.09 | https://www.gov.cn/zhengce/zhengceku/2010-12/09/content_7975.htm |
| 167 | 国办发〔1993〕48 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing Plan of the Ministry of Electronic Industry" | 2010.12.09 | https://www.gov.cn/zhengce/zhengceku/2010-12/09/content_7972.htm |
| 168 | 国办发〔1998〕82 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Coal Industry" | 2010.11.23 | https://www.gov.cn/zhengce/zhengceku/2010-11/23/content_2041.htm |
| 169 | 国办发〔1998〕81 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Forestry Administration" | 2010.11.23 | https://www.gov.cn/zhengce/zhengceku/2010-11/23/content_7764.htm |
| 170 | 国办发〔1998〕59 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Metallurgical Industry" | 2010.11.22 | https://www.gov.cn/zhengce/zhengceku/2010-11/22/content_7754.htm |
| 171 | 国办发〔1998〕53 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Light Industry" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7780.htm |
| 172 | 国办发〔1998〕55 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Building Materials Industry" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7776.htm |
| 173 | 国办发〔1998〕56 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Textile Industry" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7772.htm |
| 174 | 国办发〔1998〕57 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Machinery Industry" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7766.htm |
| 175 | 国办发〔1998〕58 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Nonferrous Metals Industry" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7762.htm |
| 176 | 国办发〔1998〕54 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the State Bureau of Petroleum and Chemical Industry" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7744.htm |
| 177 | 国办发〔1998〕88 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the Ministry of Agriculture" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7742.htm |
| 178 | 国办发〔1998〕100 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing of the Ministry of Information Industry" | 2010.11.18 | https://www.gov.cn/zhengce/zhengceku/2010-11/18/content_7724.htm |
| 179 | 国办发〔1994〕79 | Notice on Issuing the "Functional Allocation, Internal Organizations and Staffing Plan of the Ministry of Agriculture" | 2010.11.15 | https://www.gov.cn/zhengce/zhengceku/2010-11/15/content_7858.htm |
| 180 | 国办发〔1995〕45 | Notice on Enriching Workers' Spare-Time Life After the Implementation of the New Working-Hours System | 2010.11.12 | https://www.gov.cn/zhengce/zhengceku/2010-11/12/content_1343.htm |

*Note:* Several of the above are older documents retroactively re-published on the
portal; their "publish date" column reflects the portal's re-release date, while
the document number (`Doc. No.`) preserves the original issuance year.

## III. National Statistical Communiqué Data Tables (4 annual editions, 126 CSV + 4 XLSX)

- Source: National Bureau of Statistics (stats.gov.cn) annual "National Economic and Social Development Statistical Communiqué".
- Licensing basis: government open information.

| Year | Communiqué URL | Stored as |
|---|---|---|
| 2025 | https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html | stats_communique_2025.xlsx + 32 table CSVs |
| 2024 | https://www.stats.gov.cn/sj/zxfb/202502/t20250228_1958817.html | stats_communique_2024.xlsx + 32 table CSVs |
| 2023 | https://www.stats.gov.cn/sj/zxfb/202402/t20240229_1947915.html | stats_communique_2023.xlsx + 32 table CSVs |
| 2022 | https://www.stats.gov.cn/sj/zxfb/202302/t20230206_1902000.html | stats_communique_2022.xlsx + 32 table CSVs |

## IV. Totals

Total corpus (after ingestion, by format family; see `stats_build.json`):
318 source files / 7,591 logical pages (lines) / 4,976,658 Chinese characters / 14,076 chunks.

Generated: 2026-09-23 15:30
