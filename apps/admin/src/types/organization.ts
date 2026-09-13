/** design.md §7.5 / decisions.md #59(I2) Organization — schema.md `organizations`
 * 테이블과 1:1 매핑. B2G 시설(요양원·복지관) 테넌시 안전망의 기준 엔티티. */
export interface Organization {
  id: string;
  name: string;
  createdAt: string;
}
