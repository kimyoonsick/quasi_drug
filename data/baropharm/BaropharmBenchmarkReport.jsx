import ReportLayout from '../common/ReportLayout';
import { EditableField } from '../common/EditableField';
import {
    NAVY, NAVY_DARK, NAVY_LIGHT, BG_LIGHT, TEXT_MAIN, TEXT_SUB, ACCENT, BORDER,
    section, sTitle, tbl, thStyle, thR, thC, tdStyle, tdR, tdC, tdBold,
    zebraRow, execSummaryGrad, execLabel,
    kpiCard, kpiLabel, kpiValue, kpiSub, kpiGrid,
    callout, subHeading, sourceSection, sourceLabel, sourceList,
} from './reportStyles';

/* ════════════════════════════════════════════════════════
   바로팜 캠페인 원본 이미지 (public/images/baropharm/)
   ════════════════════════════════════════════════════════ */
const BARO_IMAGES = [
    { src: '/images/baropharm/baro-100won-coffee.jpg', label: '100원 커피 이벤트', desc: '연동몰 첫만남 — 연동+주문 시 스타벅스 아메리카노 100원' },
    { src: '/images/baropharm/baro-roulette.png', label: '100% 당첨 룰렛 이벤트', desc: '매일 1회 룰렛 참여 — 트래픽 확보 및 락인(Lock-in) 유도' },
    { src: '/images/baropharm/baro-spring-gamification.png', label: '봄인해제 게이미피케이션', desc: '벚꽃잎 수집형 미션 — 8개 꽃잎 완성 시 보상 지급' },
    { src: '/images/baropharm/baro-spring-rewards.png', label: '봄인해제 보상 체계', desc: '브랜드관 5%, 필렌즈 150P, 셀링리뷰 1,200P, 커넥트 명찰 지급' },
    { src: '/images/baropharm/baro-bpcs-benefit.jpg', label: 'BPCS 처방전 지원', desc: '3-Step 에스컬레이팅: 1,000P → 5,000P+쿠폰 → 10,000P' },
    { src: '/images/baropharm/baro-royal-blue-card.jpg', label: '로얄블루M 카드 제휴', desc: '우리카드 제휴 — 1.7% 적립 + 최대 38만원 혜택' },
    { src: '/images/baropharm/baro-membership-pass.jpg', label: '봄맞이 멤버십 PASS', desc: '3개월 → 1개월 등급 산정 단축 — 6단계 등급 체계' },
    { src: '/images/baropharm/baro-cmg-review.jpg', label: 'CMG제약 리뷰 이벤트', desc: '제약사 협업 — 리뷰 500P, 포토리뷰 배민 1만원권' },
];

/* ════════════════════════════════════════════════════════
   비교 매트릭스 데이터 및 스타일 (IT 경쟁분석 템플릿 참조)
   ════════════════════════════════════════════════════════ */
const MATRIX_DATA = [
    {
        campaign: '100원 커피',
        feature: '2-Step 액션 기반 보상',
        target: '신규 가입자 (Active User 확보)',
        hurdle: '중 (연동+주문)',
        reward: '스타벅스 아메리카노 (100원)',
        participation: '약 22명 (매우 저조)',
        cons: '1회성 체리피커 유입 리스크',
    },
    {
        campaign: '100% 당첨 룰렛',
        feature: '매일 즉각적 보상 (확률형)',
        target: '전체 유저 (DAU 증대/락인)',
        hurdle: '최하 (단순 클릭)',
        reward: '포인트 (10P~10,000P 랜덤)',
        participation: '확인 불가',
        cons: '실구매 전환율(CVR) 담보 불가',
    },
    {
        campaign: '처방전 지원 (BPCS)',
        feature: '단계별 보상 점증 설계',
        target: '시스템 미사용 약국',
        hurdle: '최상 (실제 처방전 수신)',
        reward: '최대 10,000P + 50% 쿠폰',
        participation: '확인 불가',
        cons: '초기 세팅의 물리적 저항감',
    },
    {
        campaign: '멤버십 PASS',
        feature: '단기 실적 기반 등급 상향',
        target: '중위/하위 등급 유저',
        hurdle: '상 (실제 매입 실적 필요)',
        reward: '상위 등급 혜택 조기 적용',
        participation: '0명 (참여 전무)',
        cons: '달성 조건이 명확하지 않거나 매력도 부족',
    },
    {
        campaign: '미션 대시보드',
        feature: '옴니채널 미션 & 미완성 효과',
        target: '충성 고객 (크로스 플랫폼)',
        hurdle: '상 (APP/PC 다중 미션)',
        reward: '미션별 차등 포인트',
        participation: '확인 불가',
        cons: '과도한 팝업 시 피로도 증가',
    },
    {
        campaign: '봄인해제',
        feature: '수집형 시각적 게이미피케이션',
        target: '흥미 위주 라이트 유저',
        hurdle: '중 (8종 액션 완료)',
        reward: '보상형 명찰 및 캐시백',
        participation: '확인 불가',
        cons: '이벤트 설계/개발 리소스 과다',
    }
];

/* ════════════════════════════════════════════════════════
   기타 데이터
   ════════════════════════════════════════════════════════ */
const PICO_STRATEGY_DATA = [
    {
        phase: '단기 (Phase 1)',
        strategy: '3-Step 에스컬레이팅 온보딩',
        action: '회원가입 → 약사 인증 → 첫 주문 완료 시 연계 보상',
        effect: '구매 전환율(CVR) 개선',
        defense: '사업자번호 단위 제한 (체리피커 차단)'
    },
    {
        phase: '단기 (Phase 1)',
        strategy: '피코몰 룰렛 (가칭)',
        action: '로그인/구매액 조건 연동형 데일리 포인트 룰렛',
        effect: '매일 방문 트래픽(DAU) 락인 유도',
        defense: '자체 쿠폰 지급 및 7일 내 유효기간 자동 소멸'
    },
    {
        phase: '중기 (Phase 2)',
        strategy: '약사 공감형 시즌 캠페인',
        action: '가정의 달, 여름 휴가 등 시의성 높은 감성 카피 적용',
        effect: '고객 유대감 형성 및 시즌 매출 방어',
        defense: '선착순 수량 한정 및 소멸 전 자동 푸시 발송'
    },
    {
        phase: '장기 (Phase 3)',
        strategy: '수집형 시각적 게이미피케이션',
        action: '자사 마스코트 IP 기반 특정 기간 미션 오브젝트 수집',
        effect: '지속적 참여 및 충성도(LTV) 극대화',
        defense: '참여 횟수 제한 및 매크로 방지 로직 적용'
    }
];

/* ════════════════════════════════════════════════════════
   메인 보고서
   ════════════════════════════════════════════════════════ */
export default function BaropharmBenchmarkReport({ titleOverride }) {
    return (
        <ReportLayout
            type="분석 보고서"
            title="[피코몰] 바로팜 벤치마크 및 피코몰 적용 전략 (1차)"
            subtitle="바로팜 핵심 캠페인 경쟁분석 매트릭스 · 3단계 적용 로드맵"
            date="2026.04.20"
            version="v1.1"
            audience="마케팅팀"
            titleOverride={titleOverride}
        >
            <div className="report-tab-content" style={{ paddingTop: '1rem' }}>

                {/* ═══ Executive Summary ═══ */}
                <section style={section}>
                    <div style={execSummaryGrad}>
                        <div style={execLabel}>EXECUTIVE SUMMARY</div>
                        <ul style={{ margin: 0, paddingLeft: '1.25rem', listStyle: 'disc', lineHeight: 2 }}>
                            <li>바로팜의 신규 <strong>룰렛 이벤트</strong>를 포함한 핵심 캠페인을 IT 경쟁분석 매트릭스로 구조화하여, 각 전략의 강점과 약점(Cons)을 명확히 대조함.</li>
                            <li>피코몰 현황 대비 <strong>최우선 도입 과제</strong>: (1) 행동 기반 리워드 퍼널 설계, (2) 게이미피케이션(룰렛/미션)을 통한 DAU 확보.</li>
                            <li>단순 트래픽(체리피커) 유입 리스크를 방어하기 위해, <strong>사업자번호 기반 어뷰징 차단</strong> 및 <strong>익월 재구매 트리거</strong>를 필수로 연동해야 함.</li>
                        </ul>
                    </div>
                </section>

                {/* ═══ 바로팜 캠페인 원본 자료 ═══ */}
                <section style={section}>
                    <h2 style={sTitle}><EditableField id="BaroBench_sTitle_gallery" fallback="바로팜 캠페인 원본 자료 (이미지)" /></h2>
                    <div style={{ fontSize: '0.8125rem', color: TEXT_SUB, marginBottom: '1rem', lineHeight: 1.7 }}>
                        아래 이미지는 바로팜의 2026년 4월 기준 공개 프로모션 화면을 캡처한 원본 자료입니다.
                    </div>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                        gap: '1rem',
                    }}>
                        {BARO_IMAGES.map((img, i) => (
                            <div key={i} style={{
                                border: `1px solid ${BORDER}`,
                                borderRadius: '4px',
                                overflow: 'hidden',
                                background: '#fff',
                            }}>
                                <div style={{
                                    width: '100%',
                                    height: '260px',
                                    overflow: 'hidden',
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    justifyContent: 'center',
                                    background: BG_LIGHT,
                                    cursor: 'pointer',
                                }} onClick={() => window.open(img.src, '_blank')}>
                                    <img
                                        src={img.src}
                                        alt={img.label}
                                        style={{
                                            width: '100%',
                                            objectFit: 'cover',
                                            objectPosition: 'top',
                                        }}
                                    />
                                </div>
                                <div style={{ padding: '0.625rem 0.75rem' }}>
                                    <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: TEXT_MAIN, marginBottom: '0.25rem' }}>
                                        {img.label}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: TEXT_SUB, lineHeight: 1.5 }}>
                                        {img.desc}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* ═══ 바로팜 캠페인 벤치마크 매트릭스 ═══ */}
                <section style={section}>
                    <h2 style={sTitle}><EditableField id="BaroBench_sTitle_matrix" fallback="캠페인 경쟁분석 벤치마크 매트릭스" /></h2>
                    <table style={tbl}>
                        <thead>
                            <tr>
                                <th style={{ ...thC, width: '120px' }}>캠페인</th>
                                <th style={thStyle}>핵심 강점 (Feature)</th>
                                <th style={thStyle}>타겟 유도행동 (Best For)</th>
                                <th style={thC}>난이도 (Hurdle)</th>
                                <th style={thStyle}>리워드 (Reward)</th>
                                <th style={thC}>참여 현황</th>
                                <th style={thStyle}>리스크 및 한계 (Cons)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {MATRIX_DATA.map((row, i) => (
                                <tr key={i} style={zebraRow(i)}>
                                    <td style={{ ...tdC, fontWeight: 700 }}>{row.campaign}</td>
                                    <td style={{ ...tdStyle, fontWeight: 600 }}>{row.feature}</td>
                                    <td style={tdStyle}>{row.target}</td>
                                    <td style={tdC}>{row.hurdle}</td>
                                    <td style={tdStyle}>{row.reward}</td>
                                    <td style={{ ...tdC, fontWeight: row.participation.includes('저조') || row.participation.includes('전무') ? 700 : 400, color: row.participation.includes('저조') || row.participation.includes('전무') ? ACCENT : TEXT_MAIN }}>
                                        {row.participation}
                                    </td>
                                    <td style={{ ...tdStyle, color: TEXT_SUB }}>{row.cons}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div style={{ ...callout, marginTop: '1rem' }}>
                        <strong>데이터 인사이트:</strong> 100원 커피 및 멤버십 PASS 캠페인의 <strong>실제 참여자가 각각 약 22명, 0명으로 매우 저조</strong>함이 확인되었습니다. 이는 체리피커 유입의 한계성 및 복잡한 참여 조건이 지닌 장애물을 시사합니다. 향후 피코몰 캠페인 기획 시 이를 반면교사 삼아 직관적이고 실제 구매 전환을 일으킬 수 있는 보상 체계를 설계해야 합니다.
                    </div>
                </section>

                {/* ═══ 피코몰 도입 및 적용 방안 (통합 테이블) ═══ */}
                <section style={section}>
                    <h2 style={sTitle}><EditableField id="BaroBench_sTitle_roadmap" fallback="피코몰 마케팅 캠페인 적용 방안" /></h2>
                    <div style={{ fontSize: '0.8125rem', color: TEXT_SUB, marginBottom: '1rem', lineHeight: 1.7 }}>
                        위의 경쟁분석을 바탕으로 피코몰에 시기별로 적용할 통합 로드맵 및 방어 정책입니다.
                    </div>
                    <table style={tbl}>
                        <thead>
                            <tr>
                                <th style={{ ...thC, width: '110px' }}>시점</th>
                                <th style={{ ...thStyle, width: '170px' }}>전략 명칭</th>
                                <th style={thStyle}>핵심 액션 (Action)</th>
                                <th style={thStyle}>기대 효과 (Effect)</th>
                                <th style={thStyle}>어뷰징 방어 정책</th>
                            </tr>
                        </thead>
                        <tbody>
                            {PICO_STRATEGY_DATA.map((s, i) => (
                                <tr key={i} style={zebraRow(i)}>
                                    <td style={{ ...tdC, fontWeight: 700 }}>{s.phase}</td>
                                    <td style={{ ...tdStyle, fontWeight: 600 }}>{s.strategy}</td>
                                    <td style={tdStyle}>{s.action}</td>
                                    <td style={tdStyle}>{s.effect}</td>
                                    <td style={{ ...tdStyle, color: TEXT_SUB }}>{s.defense}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div style={{ ...callout, marginTop: '1rem' }}>
                        <strong>차별화 포인트:</strong> 바로팜이 커피 등 범용 아이템을 미끼로 삼아 일회성 유입에 그치는 반면, 피코몰은 <strong>약국 경영에 실질적으로 필요한 실무 아이템(에코백, 샘플 등)</strong>과 <strong>자체 포인트</strong>를 리워드로 지급하여 외부 유출을 막고 실구매 전환율을 최적화합니다.
                    </div>
                </section>

                {/* ═══ 출처 ═══ */}
                <div style={sourceSection}>
                    <div style={sourceLabel}>DATA SOURCES</div>
                    <ul style={sourceList}>
                        <li>[외부] 바로팜 공개 프로모션 이미지 (2026.04 기준)</li>
                        <li>[내부] 피코몰 현황 마케팅팀 내부 분석 (2026.04.19)</li>
                    </ul>
                </div>
                
                <div style={{ fontSize: '11px', color: TEXT_SUB, textAlign: 'right', marginTop: '1rem' }}>
                    * 본 벤치마크 매트릭스는 아이디어 도출을 위한 참고 자료이며, 경품 및 룰렛 보상 기획 시 약사법 상 경제적 이익 제공 허용 범위(사은품 규정) 내에서 설계되어야 합니다.
                </div>
            </div>
        </ReportLayout>
    );
}

