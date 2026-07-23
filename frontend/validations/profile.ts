import { z } from "zod";

export const profileSchema = z.object({
  full_name: z
    .string()
    .min(2, "Full name must be at least 2 characters")
    .max(100, "Full name must be at most 100 characters")
    .nullable()
    .or(z.literal("")),
  timezone: z
    .string()
    .min(1, "Timezone is required")
    .nullable()
    .or(z.literal("")),
  date_of_birth: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Please enter a valid date in YYYY-MM-DD format")
    .nullable()
    .or(z.literal("")),
  time_of_birth: z
    .string()
    .regex(/^\d{2}:\d{2}(:\d{2})?$/, "Please enter a valid time in HH:MM format")
    .nullable()
    .or(z.literal("")),
  birth_place: z
    .string()
    .max(200, "Birth place must be at most 200 characters")
    .nullable()
    .or(z.literal("")),
  latitude: z
    .string()
    .refine((val) => {
      if (val === "" || val === null || val === undefined) return true;
      const num = Number(val);
      return !isNaN(num) && num >= -90 && num <= 90;
    }, "Latitude must be between -90 and 90")
    .nullable()
    .or(z.literal("")),
  longitude: z
    .string()
    .refine((val) => {
      if (val === "" || val === null || val === undefined) return true;
      const num = Number(val);
      return !isNaN(num) && num >= -180 && num <= 180;
    }, "Longitude must be between -180 and 180")
    .nullable()
    .or(z.literal("")),
  ayanamsa: z
    .string()
    .nullable()
    .or(z.literal("")),
  avatar_url: z
    .string()
    .nullable()
    .or(z.literal(""))
    .optional(),
  gender: z
    .string()
    .max(20, "Gender must be at most 20 characters")
    .nullable()
    .or(z.literal("")),
});

export type ProfileFormData = z.infer<typeof profileSchema>;
