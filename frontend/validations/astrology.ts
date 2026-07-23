import { z } from "zod";

export const birthDataSchema = z.object({
  date: z.string().min(1, "Birth date and time are required"),
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
  timezone: z.string().min(1, "Timezone is required"),
  ayanamsa: z.string().min(1, "Ayanamsa is required"),
  house_system: z.coerce.number().min(1),
});

export type BirthDataFormData = z.infer<typeof birthDataSchema>;
