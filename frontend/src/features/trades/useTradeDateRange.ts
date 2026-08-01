import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";

import { getTradeDateRange } from "../../api/engineClient";

export function useTradeDateRange() {
  const query = useQuery({ queryKey: ["trade-date-range"], queryFn: getTradeDateRange });
  const from = query.data?.from_time ? dayjs(query.data.from_time).startOf("day") : null;
  const to = query.data?.to_time ? dayjs(query.data.to_time).endOf("day") : null;
  return { ...query, from, to, hasTrades: Boolean(from && to) };
}
